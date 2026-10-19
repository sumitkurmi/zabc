const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

  // Login as admin
  await page.goto('http://localhost:5173/admin/login');
  await page.fill('input[type="text"]', 'admin');
  await page.fill('input[type="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1000);

  // Navigate to chats
  await page.goto('http://localhost:5173/admin/chats');
  await page.waitForTimeout(1000);

  // Click on the first chat
  const firstChatRow = page.locator('table tbody tr').first();
  if (await firstChatRow.count() > 0) {
    await firstChatRow.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/home/jules/verification/screenshots/markdown_admin_desktop.png', fullPage: true });
  }

  // Mobile viewport screenshot
  const mobilePage = await browser.newPage({ viewport: { width: 360, height: 740 } });
  await mobilePage.goto('http://localhost:5173/');
  await mobilePage.waitForTimeout(1000);
  await mobilePage.screenshot({ path: '/home/jules/verification/screenshots/markdown_mobile_360.png' });

  await browser.close();
  console.log('Screenshots captured successfully.');
})();
