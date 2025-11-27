const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

// 1. Allow All Origins (Public Proxy Mode)
app.use(cors({
    origin: '*', 
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'X-MBX-APIKEY'],
    credentials: false 
}));

// 2. Health Check
app.get('/', (req, res) => {
    res.send('Quantum Proxy is Running on Glitch!');
});

// 3. Proxy Logic
const proxyOptions = {
    target: 'https://api.binance.com',
    changeOrigin: true,
    pathRewrite: {
        '^/api/v3': '/api/v3'
    },
    onProxyRes: (proxyRes) => {
        // Strip restrictive headers from Binance so browser accepts response
        delete proxyRes.headers['access-control-allow-origin'];
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
    }
};

app.use('/api', createProxyMiddleware(proxyOptions));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
