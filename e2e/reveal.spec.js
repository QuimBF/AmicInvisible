const { test, expect } = require('@playwright/test')
const { execFileSync } = require('node:child_process')
const { readFileSync } = require('node:fs')

const PREFIX = 'Et toca fer el regal a: '
const ERROR = 'Aquest enllaç no porta cap codi vàlid'
const NAMES = JSON.parse(readFileSync('grups.example.json', 'utf8')).flat()

const out = execFileSync('python3', ['sorteig.py', 'http://127.0.0.1:4173/', '--grups', 'grups.example.json'], { encoding: 'utf8' })
const links = [...out.matchAll(/^--- (.+) ---\n(\S+)$/gm)].map(([, giver, url]) => {
  const text = Buffer.from(url.split('#')[1], 'hex').toString('utf8')
  return { giver, url, receiver: text.slice(PREFIX.length).trimEnd() }
})

test('every example person gets a link', () => {
  expect(links.map((l) => l.giver).sort()).toEqual([...NAMES].sort())
})

for (const { giver, url, receiver } of links) {
  test(`reveal for ${giver}`, async ({ page }) => {
    await page.goto(url)
    const name = page.locator('#nom')
    const button = page.getByRole('button', { name: 'Descobreix-ho' })

    await expect(button).toBeVisible()
    await expect(name).toBeEmpty()
    const before = await page.locator('body').innerText()
    for (const n of NAMES) expect(before).not.toContain(n)

    // Centred-ish: button centre within 15% of the viewport centre on both axes.
    const box = await button.boundingBox()
    const vp = page.viewportSize()
    expect(Math.abs(box.x + box.width / 2 - vp.width / 2)).toBeLessThan(vp.width * 0.15)
    expect(Math.abs(box.y + box.height / 2 - vp.height / 2)).toBeLessThan(vp.height * 0.15)

    await button.click()
    await expect(name).toBeVisible()
    await expect(name).toContainText(receiver)
    expect(NAMES).toContain(receiver)
    expect(receiver).not.toBe(giver)
  })
}

for (const [label, path] of [['invalid hash', '/#zz'], ['missing hash', '/']]) {
  test(`${label} shows the error`, async ({ page }) => {
    await page.goto(path)
    await expect(page.getByText(ERROR)).toBeVisible()
    await expect(page.getByRole('button')).toHaveCount(0)
  })
}

test('no horizontal scroll', async ({ page }) => {
  await page.goto(links[0].url)
  await page.getByRole('button', { name: 'Descobreix-ho' }).click()
  const [scroll, width] = await page.evaluate(() => [document.scrollingElement.scrollWidth, innerWidth])
  expect(scroll).toBeLessThanOrEqual(width)
})

test.describe('reduced motion', () => {
  test.use({ reducedMotion: 'reduce' })
  test('name visible right after click', async ({ page }) => {
    await page.goto(links[0].url)
    await page.getByRole('button', { name: 'Descobreix-ho' }).click()
    expect(await page.locator('#nom').evaluate((el) => getComputedStyle(el).opacity)).toBe('1')
  })
})

test('everyone is told it is one gift, one budget', async ({ page }) => {
  await page.goto('/#' + Buffer.from(PREFIX + 'Pere').toString('hex'))
  await page.getByRole('button', { name: 'Descobreix-ho' }).click()
  await expect(page.locator('#nom small')).toContainText('un sol regal')
})
