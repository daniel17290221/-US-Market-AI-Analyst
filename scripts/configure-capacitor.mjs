import { writeFile } from 'node:fs/promises';

const origin = process.env.CAPACITOR_SERVER_URL?.trim().replace(/\/+$/, '');
const allowCleartext = process.env.CAPACITOR_ALLOW_CLEARTEXT === '1';

if (origin?.startsWith('http://') && !allowCleartext) {
  throw new Error(
    'CAPACITOR_SERVER_URL must use HTTPS. Set CAPACITOR_ALLOW_CLEARTEXT=1 only for local development.',
  );
}

const config = {
  appId: 'com.vibecodinglab.dividend',
  appName: '배당 투자',
  webDir: 'mobile-shell',
  android: {
    allowMixedContent: false,
  },
};

if (origin) {
  const appUrl = `${origin}/dividend?source=capacitor`;
  config.server = {
    url: appUrl,
    cleartext: allowCleartext,
    allowNavigation: [new URL(appUrl).hostname],
  };
}

await writeFile(
  new URL('../capacitor.config.json', import.meta.url),
  `${JSON.stringify(config, null, 2)}\n`,
  'utf8',
);

console.log(
  origin
    ? `Capacitor server configured: ${origin}`
    : 'Capacitor fallback shell configured (CAPACITOR_SERVER_URL is not set).',
);
