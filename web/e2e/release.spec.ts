import { test, expect } from '@playwright/test'

const viewports = [
  { width: 390, height: 844, name: 'phone' },
  { width: 768, height: 1024, name: 'tablet' },
  { width: 1440, height: 900, name: 'desktop' },
]

async function expectNoHorizontalOverflow(page: import('@playwright/test').Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow, `horizontal overflow ${overflow}px`).toBeLessThanOrEqual(1)
}

for (const viewport of viewports) {
  test(`${viewport.name} core routes stay responsive`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height })
    for (const path of ['/', '/stays', '/store', '/account']) {
      await page.goto(path)
      await expect(page.locator('body')).toBeVisible()
      await expectNoHorizontalOverflow(page)
    }
  })
}

test('keyboard and reduced motion keep primary navigation functional', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' })
  // Playwright context option is named reducedMotion; emulateMedia validates the same user preference.
  await page.goto('/')
  let reached=false
  for (let i=0;i<16;i+=1) {
    await page.keyboard.press('Tab')
    const text=await page.evaluate(() => document.activeElement?.textContent ?? '')
    if (/BOOK A STAY/i.test(text)) { reached=true; break }
  }
  expect(reached).toBeTruthy()
})

test('metadata and canonical link are present on core public pages', async ({ page }) => {
  for (const path of ['/', '/stays', '/store']) {
    await page.goto(path)
    await expect(page).toHaveTitle(/Livenza/i)
    await expect(page.locator('meta[name="description"]')).toHaveAttribute('content', /.+/)
    await expect(page.locator('link[rel=canonical]')).toHaveCount(1)
  }
})

test('unknown route has a usable 404', async ({ page }) => {
  const response=await page.goto('/definitely-not-a-livenza-route')
  expect(response?.status()).toBe(404)
  await expect(page.getByRole('heading',{name:/Page not found/i})).toBeVisible()
  await expect(page.getByRole('link',{name:/Return home/i})).toBeVisible()
})
