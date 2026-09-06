from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parents[1]
API_SOURCE = (ROOT / 'livenza_api_v1.py').read_text(encoding='utf-8')
APP_SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')


def _login(client, mobile):
    requested = client.post('/api/v1/auth/otp/request', json={'mobile': mobile})
    assert requested.status_code == 202
    otp = requested.get_json()['test_otp']
    verified = client.post('/api/v1/auth/otp/verify', json={'mobile': mobile, 'otp': otp})
    assert verified.status_code == 200
    return verified.get_json()['customer']


def _cleanup(app_module):
    with app_module.app.app_context():
        for name in ('FitConnection', 'FitPlan', 'FitHealthLog', 'FitWorkout', 'FitProfile'):
            model = getattr(app_module, name, None)
            if model is not None:
                model.query.delete()
        app_module.CustomerSession.query.delete()
        app_module.CustomerOtpChallenge.query.delete()
        app_module.CustomerIdentity.query.delete()
        app_module.CustomerAddress.query.delete()
        app_module.Customer.query.delete()
        app_module.db.session.commit()


def test_fit_models_and_api_registration_are_present():
    for model_name in ('FitProfile', 'FitWorkout', 'FitHealthLog', 'FitPlan', 'FitConnection'):
        assert f'class {model_name}(db.Model):' in APP_SOURCE
        assert f"'{model_name}': {model_name}" in APP_SOURCE
        assert f'{model_name} = models["{model_name}"]' in API_SOURCE
    for route in ('/fit/profile', '/fit/workouts', '/fit/health/logs', '/fit/plans', '/fit/integrations'):
        assert route in API_SOURCE


def test_fit_routes_require_authenticated_customer(client, app_module):
    _cleanup(app_module)
    for method, route in (
        ('get', '/api/v1/fit/profile'),
        ('get', '/api/v1/fit/workouts'),
        ('get', '/api/v1/fit/health/logs'),
        ('get', '/api/v1/fit/plans'),
        ('get', '/api/v1/fit/integrations'),
    ):
        response = getattr(client, method)(route)
        assert response.status_code == 401


def test_fit_profile_defaults_and_update_are_customer_scoped(client, app_module, monkeypatch):
    _cleanup(app_module)
    monkeypatch.setenv('CUSTOMER_AUTH_TEST_MODE', '1')
    monkeypatch.setenv('FLASK_ENV', 'test')
    _login(client, '9876502201')
    initial = client.get('/api/v1/fit/profile')
    assert initial.status_code == 200
    assert initial.get_json()['profile']['units'] == 'metric'
    updated = client.put('/api/v1/fit/profile', json={
        'units': 'metric', 'height_cm': 178, 'default_rep_seconds': 3.5, 'goal': 'strength'
    })
    assert updated.status_code == 200
    profile = updated.get_json()['profile']
    assert profile['height_cm'] == 178.0
    assert profile['default_rep_seconds'] == 3.5
    assert profile['goal'] == 'strength'
    bad = client.put('/api/v1/fit/profile', json={'default_rep_seconds': 0.1})
    assert bad.status_code == 400
    _cleanup(app_module)


def test_fit_workout_post_is_idempotent_and_owner_scoped(client, app_module, monkeypatch):
    _cleanup(app_module)
    monkeypatch.setenv('CUSTOMER_AUTH_TEST_MODE', '1')
    monkeypatch.setenv('FLASK_ENV', 'test')
    first = _login(client, '9876502202')
    payload = {
        'client_record_id': 'device-workout-1',
        'exercise_id': 'push-up',
        'exercise_name': 'Push-Up',
        'sets': 3,
        'reps': 10,
        'rep_seconds': 3.5,
        'duration_seconds': 105,
        'estimated_calories': 20.2,
        'completed_at': '2026-09-06T04:00:00Z',
    }
    created = client.post('/api/v1/fit/workouts', json=payload)
    assert created.status_code == 201
    repeated = client.post('/api/v1/fit/workouts', json=payload)
    assert repeated.status_code == 200
    assert repeated.get_json()['workout']['id'] == created.get_json()['workout']['id']
    with app_module.app.app_context():
        owner = app_module.Customer.query.filter_by(primary_mobile=first['primary_mobile']).first()
        other = app_module.Customer(public_id='fit-other', primary_mobile='+919876502299', full_name='Other Fit')
        app_module.db.session.add(other); app_module.db.session.flush()
        app_module.db.session.add(app_module.FitWorkout(
            customer_id=other.id, client_record_id='other-workout', exercise_id='squat', exercise_name='Squat',
            sets=1, reps=5, rep_seconds=2.0, duration_seconds=10, source='test',
            completed_at=datetime.datetime(2026, 9, 6, 4, 5, 0), metadata_json='{}'
        ))
        app_module.db.session.commit()
        assert owner is not None
    listed = client.get('/api/v1/fit/workouts')
    assert listed.status_code == 200
    ids = {row['client_record_id'] for row in listed.get_json()['items']}
    assert ids == {'device-workout-1'}
    _cleanup(app_module)


def test_fit_health_log_recomputes_bmi_and_never_trusts_client_bmi(client, app_module, monkeypatch):
    _cleanup(app_module)
    monkeypatch.setenv('CUSTOMER_AUTH_TEST_MODE', '1')
    monkeypatch.setenv('FLASK_ENV', 'test')
    _login(client, '9876502203')
    response = client.post('/api/v1/fit/health/logs', json={
        'recorded_at': '2026-09-06T04:10:00Z',
        'weight_kg': 70,
        'height_cm': 175,
        'bmi': 99,
        'steps': 5234,
        'activity_minutes': 35,
        'resting_heart_rate': 62,
        'source': 'manual',
    })
    assert response.status_code == 201
    item = response.get_json()['health_log']
    assert item['bmi'] == 22.86
    assert item['bmi'] != 99
    listed = client.get('/api/v1/fit/health/logs')
    assert listed.status_code == 200
    assert listed.get_json()['items'][0]['bmi'] == 22.86
    _cleanup(app_module)


def test_fit_native_connection_returns_safe_companion_status(client, app_module, monkeypatch):
    _cleanup(app_module)
    monkeypatch.setenv('CUSTOMER_AUTH_TEST_MODE', '1')
    monkeypatch.setenv('FLASK_ENV', 'test')
    _login(client, '9876502204')
    response = client.post('/api/v1/fit/integrations/health_connect/connect', json={})
    assert response.status_code == 202
    body = response.get_json()['connection']
    assert body['provider'] == 'health_connect'
    assert body['status'] == 'requires_companion'
    assert 'credential_ref' not in body
    assert 'token' not in str(body).lower()
    listed = client.get('/api/v1/fit/integrations')
    assert listed.status_code == 200
    assert listed.get_json()['items'][0]['provider'] == 'health_connect'
    _cleanup(app_module)
