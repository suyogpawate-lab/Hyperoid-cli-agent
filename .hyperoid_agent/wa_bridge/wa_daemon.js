import makeWASocket, { useMultiFileAuthState, DisconnectReason } from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import pino from 'pino';
import fs from 'fs';
import path from 'path';

const AUTH_DIR = path.resolve(process.env.HOME, '.hyperoid_agent/wa_bridge/auth_info');
const CMD_QUEUE_DIR = path.resolve(process.env.HOME, '.hyperoid_agent/wa_bridge/queue');

if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true });
if (!fs.existsSync(CMD_QUEUE_DIR)) fs.mkdirSync(CMD_QUEUE_DIR, { recursive: true });

let sock;

async function startWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);

    sock = makeWASocket({
        auth: state,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: false
    });

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n\x1b[1;36m+===================================================+\x1b[0m');
            console.log('\x1b[1;36m|     SCAN THIS QR CODE IN WHATSAPP LINKED DEVICES   |\x1b[0m');
            console.log('\x1b[1;36m+===================================================+\x1b[0m\n');
            qrcode.generate(qr, { small: true });
        }

        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
            if (shouldReconnect) {
                setTimeout(startWhatsApp, 3000);
            }
        }
    });

    sock.ev.on('creds.update', saveCreds);
}

setInterval(async () => {
    if (!sock) return;
    try {
        const files = fs.readdirSync(CMD_QUEUE_DIR);
        for (const file of files) {
            if (file.endsWith('.json')) {
                const filePath = path.join(CMD_QUEUE_DIR, file);
                const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                const cleanPhone = data.phone.replace(/[^0-9]/g, '');
                const jid = `${cleanPhone}@s.whatsapp.net`;
                await sock.sendMessage(jid, { text: data.text });
                fs.unlinkSync(filePath);
            }
        }
    } catch (err) {}
}, 1000);

startWhatsApp();

