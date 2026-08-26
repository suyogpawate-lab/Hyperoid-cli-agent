// Optional WhatsApp queue worker. Run only after npm install in this directory.
import makeWASocket,{useMultiFileAuthState,DisconnectReason} from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal'; import pino from 'pino'; import fs from 'fs'; import path from 'path';
const home=process.env.HOME, auth=path.join(home,'.hyperoid_agent/wa_bridge/auth_info'), queue=path.join(home,'.hyperoid_agent/wa_bridge/queue');
fs.mkdirSync(auth,{recursive:true}); fs.mkdirSync(queue,{recursive:true}); let sock;
async function start(){const {state,saveCreds}=await useMultiFileAuthState(auth); sock=makeWASocket({auth:state,logger:pino({level:'silent'}),printQRInTerminal:false}); sock.ev.on('creds.update',saveCreds); sock.ev.on('connection.update',u=>{if(u.qr)qrcode.generate(u.qr,{small:true}); if(u.connection==='close' && u.lastDisconnect?.error?.output?.statusCode!==DisconnectReason.loggedOut)setTimeout(start,3000);});}
setInterval(async()=>{if(!sock)return; for(const f of fs.readdirSync(queue).filter(x=>x.endsWith('.json'))){const p=path.join(queue,f); try{const d=JSON.parse(fs.readFileSync(p)); const n=String(d.phone).replace(/\D/g,''); await sock.sendMessage(`${n}@s.whatsapp.net`,{text:String(d.text)}); fs.unlinkSync(p);}catch(e){console.error(e);}}},1000); start();
