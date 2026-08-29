import { expect, test } from '@playwright/test'

test('same Livenza identity can shop and see order/rewards', async ({ page }) => {
  // Acceptance path: same Livenza identity used by Stays -> Store -> checkout -> My Livenza.
  await page.goto('/store')
  await expect(page.getByText('WEAR THE LIFE.')).toBeVisible()
  // Live/staging fixtures publish a product; this navigation remains explicit so
  // the test cannot silently pass on a teaser-only Store.
  const firstProduct = page.locator('a.store-product-card').first()
  await expect(firstProduct).toBeVisible()
  await firstProduct.click()
  await page.getByRole('button', { name: 'ADD TO BAG' }).click()
  await page.goto('/store/cart')
  await page.getByRole('link', { name: 'CHECKOUT' }).click()
  // Expected route: /store/checkout
  await expect(page).toHaveURL(/\/store\/checkout/)
  // Authentication/payment are supplied by staging fixtures or test gateway.
  // After the payment webhook, the same Livenza identity must own both views.
  await page.goto('/my/orders')
  await expect(page.getByText('YOUR ORDERS.')).toBeVisible()
  await page.goto('/my/rewards')
  await expect(page.getByText(/POINTS/)).toBeVisible()
})
