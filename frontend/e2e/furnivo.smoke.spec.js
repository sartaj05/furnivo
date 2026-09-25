import { test, expect } from '@playwright/test'

test('landing navigation and contact enquiry work', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('link', { name: 'Platform' }).first()).toBeVisible()
  await page.getByRole('link', { name: 'Contact' }).first().click()
  await expect(page).toHaveURL(/section=contact/)
  await expect(page.locator('#contact')).toBeVisible()
  await page.getByLabel('Name').fill('Playwright Tester')
  await page.getByLabel('Company').fill('Browser QA Studio')
  await page.getByLabel('Email').fill('qa@example.com')
  await page.getByLabel('Project details').fill('Please send a furniture workflow demo.')
  await page.getByRole('button', { name: /send enquiry/i }).click()
  await expect(page.getByText(/received|thanks/i)).toBeVisible()
})

test('demo login reaches the protected workspace', async ({ page }) => {
  await page.goto('/#/login')
  await expect(page.getByRole('heading', { name: /sign in to furnivo/i })).toBeVisible()
  await page.getByLabel('Email').fill('admin@furnivo.demo')
  await page.getByLabel('Password').fill('admin123')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/#\/app$/)
  await expect(page.getByText(/commercial movement|workspace/i).first()).toBeVisible()
})

test('workshop operator is routed to the execution-only workspace', async ({ page }) => {
  await page.goto('/#/login')
  await page.getByLabel('Email').fill('workshop@furnivo.demo')
  await page.getByLabel('Password').fill('workshop123')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/#\/app\/mobile-workshop$/)
  await expect(page.getByRole('heading', { name: /mobile workshop execution/i })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Quotations' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: /material issue|mobile workshop/i }).first()).toBeVisible()
})
