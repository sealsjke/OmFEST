import puppeteer from 'puppeteer-core';

const WEB_URL = process.env.WEB_URL || 'http://web:5000';
const LIGHTPANDA_URL = process.env.LIGHTPANDA_URL || 'ws://lightpanda:9222';
const BOSS_SECRET = process.env.BOSS_SECRET || 'boss_internal_secret_token_12345';
const WELCOME_MESSAGE = process.env.WELCOME_MESSAGE || 'Здравствуйте! Я ваш новый начальник отдела. Все служебные отчеты и вопросы направлять в данный чат. Бездельников не потерплю, жду результатов!';
const CHECK_INTERVAL = parseInt(process.env.CHECK_INTERVAL || '15', 10) * 1000;

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForWeb() {
    console.log(`[BOT] Waiting for Web service at ${WEB_URL}/health...`);
    while (true) {
        try {
            const res = await fetch(`${WEB_URL}/health`);
            if (res.ok) {
                console.log('[BOT] Web service is up and healthy!');
                return;
            }
        } catch (e) {
            // Service not ready yet
        }
        await sleep(2000);
    }
}

async function connectLightpanda() {
    console.log(`[BOT] Connecting to Lightpanda at ${LIGHTPANDA_URL}...`);
    while (true) {
        try {
            const browser = await puppeteer.connect({
                browserWSEndpoint: LIGHTPANDA_URL,
                headers: { Host: 'localhost:9222' },
            });
            console.log('[BOT] Successfully connected to Lightpanda browser!');
            return browser;
        } catch (e) {
            console.log(`[BOT] Waiting for Lightpanda (${e.message}), retrying in 2s...`);
            await sleep(2000);
        }
    }
}

async function runCheckCycle(browser) {
    let tasks;
    try {
        const res = await fetch(`${WEB_URL}/api/internal/bot/tasks?secret=${encodeURIComponent(BOSS_SECRET)}`);
        if (!res.ok) {
            console.error(`[BOT] Failed to fetch tasks from web: HTTP ${res.status}`);
            return;
        }
        tasks = await res.json();
    } catch (e) {
        console.error(`[BOT] Error querying tasks: ${e.message}`);
        return;
    }

    if (tasks.new_users && tasks.new_users.length > 0) {
        for (const user of tasks.new_users) {
            console.log(`[BOT] Sending welcoming message to new employee: ${user.username} (ID: ${user.id})...`);
            try {
                const welcomeRes = await fetch(`${WEB_URL}/api/internal/bot/send-welcome`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        secret: BOSS_SECRET,
                        user_id: user.id,
                        message: WELCOME_MESSAGE,
                    }),
                });
                if (welcomeRes.ok) {
                    console.log(`[BOT] Welcoming message delivered to ${user.username}.`);
                } else {
                    console.error(`[BOT] Failed to deliver welcoming message: HTTP ${welcomeRes.status}`);
                }
            } catch (e) {
                console.error(`[BOT] Error sending welcome message: ${e.message}`);
            }
        }
    }

    // 2. Visit active employee chats with Lightpanda (Phase 1 XSS)
    if (tasks.active_users && tasks.active_users.length > 0) {
        for (const user of tasks.active_users) {
            console.log(`[BOT] [Начальник] Inspecting dialogue with ${user.username}...`);
            let page = null;
            try {
                page = await browser.newPage();
                page.setDefaultNavigationTimeout(15000);
                page.setDefaultTimeout(15000);

                const targetUrl = `${WEB_URL}/quick-auth?token=${encodeURIComponent(BOSS_SECRET)}&as=boss&redirect=${encodeURIComponent('/chat/' + user.username)}`;
                
                await page.goto(targetUrl, { waitUntil: 'load', timeout: 12000 });
                
                // Allow JavaScript / XSS payloads to execute
                await sleep(5000);
                console.log(`[BOT] [Начальник] Finished inspecting dialogue with ${user.username}.`);
            } catch (e) {
                console.error(`[BOT] Error inspecting dialogue with ${user.username}: ${e.message}`);
            } finally {
                if (page) {
                    try {
                        await page.close();
                    } catch (_) {}
                }
            }
        }
    }

    let memoTasks;
    try {
        const memoRes = await fetch(`${WEB_URL}/api/internal/bot/pending-memos?secret=${encodeURIComponent(BOSS_SECRET)}`);
        if (memoRes.ok) {
            memoTasks = await memoRes.json();
        }
    } catch (e) {
        console.error(`[BOT] Error querying pending memos: ${e.message}`);
    }

    if (memoTasks && memoTasks.pending_memos && memoTasks.pending_memos.length > 0) {
        for (const memo of memoTasks.pending_memos) {
            console.log(`[BOT] [Генеральный директор] Reviewing memo #${memo.id}: "${memo.title}" at ${memo.url}...`);
            let page = null;
            try {
                page = await browser.newPage();
                page.setDefaultNavigationTimeout(15000);
                page.setDefaultTimeout(15000);

                const authTarget = `${WEB_URL}/quick-auth?token=${encodeURIComponent(BOSS_SECRET)}&as=director&redirect=/memos`;
                await page.goto(authTarget, { waitUntil: 'load', timeout: 12000 });

                let targetUrl = memo.url.trim();
                if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
                    targetUrl = `${WEB_URL}${targetUrl.startsWith('/') ? '' : '/'}${targetUrl}`;
                }

                console.log(`[BOT] [Генеральный директор] Opening materials URL: ${targetUrl}...`);
                await page.goto(targetUrl, { waitUntil: 'load', timeout: 12000 });

                await sleep(6000);
                console.log(`[BOT] [Генеральный директор] Finished reviewing memo #${memo.id}.`);

                await fetch(`${WEB_URL}/api/internal/bot/memo-visited`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        secret: BOSS_SECRET,
                        memo_id: memo.id,
                    }),
                });
            } catch (e) {
                console.error(`[BOT] [Генеральный директор] Error reviewing memo #${memo.id}: ${e.message}`);
            } finally {
                if (page) {
                    try {
                        await page.close();
                    } catch (_) {}
                }
            }
        }
    }
}

async function main() {
    console.log('[BOT] Initializing Начальник Bot service...');
    await waitForWeb();
    let browser = await connectLightpanda();

    while (true) {
        try {
            if (!browser || !browser.isConnected()) {
                console.log('[BOT] Browser connection lost, reconnecting...');
                browser = await connectLightpanda();
            }
            await runCheckCycle(browser);
        } catch (e) {
            console.error('[BOT] Error during check cycle:', e.message);
        }
        await sleep(CHECK_INTERVAL);
    }
}

main().catch(err => {
    console.error('[BOT] Fatal error in bot process:', err);
    process.exit(1);
});
