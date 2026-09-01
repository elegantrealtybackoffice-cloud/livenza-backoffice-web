import { test, expect, type Page } from '@playwright/test'

async function seedApi(page: Page) {
  if (process.env.PLAYWRIGHT_LIVE_API === '1') return
  await page.route('**/api/v1/cities', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [{ name: 'Jaipur' }, { name: 'Gurugram' }] }) }))
  await page.route(/.*\/api\/v1\/properties\?.*/, route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ items: [{ id: 1, slug: 'oasis-residency', name: 'Oasis Residency', city: 'Jaipur', area: 'Sitapura', summary: 'A Livenza student living property.', stay_types: ['student'] }] }) }))
  await page.route('**/api/v1/properties/oasis-residency', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ id: 1, slug: 'oasis-residency', name: 'Oasis Residency', city: 'Jaipur', area: 'Sitapura', summary: 'A Livenza student living property.', stay_types: ['student'], room_categories: [{ slug: 'deluxe-twin', name: 'Deluxe Twin', occupancy: 2, summary: 'Twin-sharing category.' }] }) }))
}

test('homepage to Jaipur property discovery works on mobile 390x844', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await seedApi(page)
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'LIVE MORE.' })).toBeVisible()
  await page.getByRole('button', { name: /open menu/i }).click()
  await page.getByRole('navigation', { name: 'Mobile' }).getByRole('link', { name: 'Stays' }).click()
  await page.getByLabel('City').selectOption('Jaipur')
  await page.getByRole('button', { name: /find stays/i }).click()
  await expect(page).toHaveURL(/city=Jaipur/)
  await expect(page.getByRole('main')).toBeVisible()
})

test('desktop discovery reaches a verified property page', async ({ page }) => {
  await seedApi(page)
  await page.goto('/stays?city=Jaipur')
  await expect(page.getByText('Oasis Residency')).toBeVisible()
  await page.getByRole('link', { name: /see rooms/i }).click()
  await expect(page.getByRole('heading', { name: 'Oasis Residency' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'CHECK AVAILABILITY' }).first()).toBeVisible()
})

test('keyboard navigation can reach the brand menu and booking action', async ({ page }) => {
  await seedApi(page)
  await page.goto('/')
  for (let index = 0; index < 12; index += 1) {
    await page.keyboard.press('Tab')
    const active = await page.evaluate(() => document.activeElement?.textContent ?? '')
    if (/BOOK A STAY/i.test(active)) return
  }
  throw new Error('keyboard Tab traversal did not reach BOOK A STAY')
})
