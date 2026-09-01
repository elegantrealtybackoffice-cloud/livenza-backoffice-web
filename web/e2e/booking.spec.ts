import { createHmac } from 'node:crypto'
import { test, expect } from '@playwright/test'

function isoDate(daysFromNow: number) {
  const d = new Date(Date.now() + daysFromNow * 24 * 60 * 60 * 1000)
  return d.toISOString().slice(0, 10)
}

test('student Book Now confirms only after signed Razorpay webhook', async ({ page, request }) => {
  const property = process.env.E2E_PROPERTY_SLUG
  const room = process.env.E2E_ROOM_CATEGORY_SLUG
  const webhookSecret = process.env.RAZORPAY_WEBHOOK_SECRET
  test.skip(!property || !room || !webhookSecret, 'E2E booking fixture environment is not configured')

  await page.route('https://checkout.razorpay.com/v1/checkout.js', async route => {
    await route.fulfill({
      contentType: 'application/javascript',
      body: `window.Razorpay=function(options){this.open=function(){setTimeout(function(){options.handler({razorpay_payment_id:'pay_e2e_test'});},30)}};`,
    })
  })

  await page.goto(`/stays/book?property=${encodeURIComponent(property!)}&room_category=${encodeURIComponent(room!)}`)
  await expect(page.getByRole('heading', { name: /choose your stay/i })).toBeVisible()

  await page.getByLabel('Move-in').fill(isoDate(7))
  await page.getByLabel('Move-out').fill(isoDate(37))
  await page.getByRole('button', { name: /check live availability/i }).click()

  await page.getByLabel('Mobile number').fill(process.env.E2E_CUSTOMER_MOBILE ?? '9876543210')
  await page.getByRole('button', { name: /send otp/i }).click()
  await expect(page.getByLabel('6-digit OTP')).toHaveValue(/\d{6}/)
  await page.getByRole('button', { name: /verify otp/i }).click()
  await page.getByRole('button', { name: /^continue$/i }).click()

  await page.getByLabel('Resident name').fill('E2E Resident')
  await page.getByLabel(/college \/ course/i).fill('E2E Course')
  await page.getByRole('button', { name: /^continue$/i }).click()

  await page.getByLabel('Guardian name').fill('E2E Guardian')
  await page.getByLabel('Guardian mobile').fill('9876543211')
  await page.getByRole('button', { name: /^continue$/i }).click()

  const moveInKit = page.getByText(/Move-In Kit/i)
  if (await moveInKit.count()) {
    const checkbox = page.getByRole('checkbox').filter({ has: moveInKit })
    if (await checkbox.count()) await checkbox.first().check()
  }
  await page.getByRole('button', { name: /^continue$/i }).click()
  await page.getByRole('button', { name: /create secure booking/i }).click()
  await expect(page.getByRole('heading', { name: /payment/i })).toBeVisible()

  const paymentResponsePromise = page.waitForResponse(response =>
    response.url().includes('/api/v1/payments') && response.request().method() === 'POST' && response.status() < 400
  )
  await page.getByRole('button', { name: /pay securely/i }).click()
  const paymentResponse = await paymentResponsePromise
  const paymentBody = await paymentResponse.json()
  const orderId = paymentBody.checkout.order_id as string

  const webhookBody = JSON.stringify({
    event: 'payment.captured',
    payload: { payment: { entity: { id: 'pay_e2e_test', order_id: orderId, status: 'captured' } } },
  })
  const signature = createHmac('sha256', webhookSecret!).update(Buffer.from(webhookBody)).digest('hex')
  const eventId = `evt_e2e_${Date.now()}`
  const webhook = await request.post('/api/v1/payments/webhooks/razorpay', {
    data: webhookBody,
    headers: {
      'Content-Type': 'application/json',
      'X-Razorpay-Signature': signature,
      'x-razorpay-event-id': eventId,
    },
  })
  expect(webhook.ok()).toBeTruthy()

  await expect(page).toHaveURL(/\/stays\/booking\//)
  await expect(page.getByRole('heading', { name: /you’re in/i })).toBeVisible({ timeout: 20_000 })
  await expect(page.getByRole('link', { name: /view receipt/i })).toBeVisible()
})
