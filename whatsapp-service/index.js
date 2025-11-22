const wppconnect = require('@wppconnect-team/wppconnect');
const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());

const PORT = 3001;
const GROUP_INVITE_CODE = 'EOwarEsjc6bIWnIQptnglz';
let client = null;
let targetGroupId = null;

// Ensure static dir exists for QR code
const QR_PATH = path.join(__dirname, '../src/static/whatsapp_qr.png');

wppconnect.create({
    session: 'alfa-ofertas',
    catchQR: (base64Qr, asciiQR) => {
        console.log(asciiQR); // Print to terminal
        // Save to file for dashboard
        const matches = base64Qr.match(/^data:([A-Za-z-+\/]+);base64,(.+)$/);
        if (matches.length !== 3) return;
        const buffer = Buffer.from(matches[2], 'base64');
        fs.writeFileSync(QR_PATH, buffer);
        console.log('QR Code saved to', QR_PATH);
    },
    logQR: false,
    headless: true,
    browserArgs: ['--no-sandbox', '--disable-setuid-sandbox']
})
    .then((wppClient) => {
        client = wppClient;
        console.log('WhatsApp Client Connected!');
        startService();
    })
    .catch((error) => console.log(error));

function startService() {
    // Try to join the group
    client.joinGroup(GROUP_INVITE_CODE)
        .then((result) => {
            console.log('Joined Group Result:', result);
            if (result && result.id) {
                targetGroupId = result.id; // Store ID
                console.log('Target Group ID set to:', targetGroupId);
            }
        })
        .catch((error) => {
            console.log('Error joining group (might already be joined):', error);
            // If already joined, we need to find the group ID.
            // We can assume the user scanned the QR and the bot is in the group.
            // We'll try to find it in getAllChats later if targetGroupId is null.
        });

    // API Endpoint to send deals
    app.post('/send-deal', async (req, res) => {
        if (!client) return res.status(503).json({ error: 'WhatsApp not ready' });

        const { deal } = req.body;
        if (!deal) return res.status(400).json({ error: 'Missing deal data' });

        try {
            let groupsToSend = [];

            if (targetGroupId) {
                groupsToSend.push({ id: { _serialized: targetGroupId }, name: 'Target Group' });
            } else {
                // Fallback: Try to find groups
                const chats = await client.getAllChats();
                if (chats && Array.isArray(chats)) {
                    const groups = chats.filter(chat => chat.isGroup);
                    // Look for "Alfa" or "Ofertas"
                    const targetGroups = groups.filter(g => g.name && (g.name.includes('Alfa') || g.name.includes('Ofertas') || g.name.includes('Promo')));
                    if (targetGroups.length > 0) {
                        groupsToSend = targetGroups;
                    } else if (groups.length > 0) {
                        groupsToSend.push(groups[0]); // Send to first group found
                    }
                }
            }

            if (groupsToSend.length === 0) {
                console.log('No groups found to send deal.');
                // Try to use the known ID from logs if all else fails
                // 120363423459795612@g.us
                groupsToSend.push({ id: { _serialized: '120363423459795612@g.us' }, name: 'Hardcoded Backup' });
            }

            const message = `*OFERTA ENCONTRADA!* 🚀\n\n` +
                `*${deal.title}*\n` +
                `💰 De: ~R$ ${deal.original_price}~\n` +
                `🔥 *Por: R$ ${deal.price}*\n` +
                `📉 Desconto: ${deal.discount}%\n` +
                `⭐ ${deal.rating}\n\n` +
                `🔗 *Link:* ${deal.link}`;

            const results = [];
            for (const group of groupsToSend) {
                console.log(`Sending to group: ${group.name} (${group.id._serialized})`);
                // Send Image first if available
                if (deal.image) {
                    await client.sendImage(group.id._serialized, deal.image, 'deal.jpg', message);
                } else {
                    await client.sendText(group.id._serialized, message);
                }
                results.push(group.name);
            }

            res.json({ success: true, sent_to: results });

        } catch (error) {
            console.error('Error sending message:', error);
            res.status(500).json({ error: error.message });
        }
    });

    app.listen(PORT, () => {
        console.log(`WhatsApp Service running on port ${PORT}`);
    });
}
