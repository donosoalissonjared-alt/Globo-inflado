const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();
const PORT = process.env.PORT || 3000;

// 1. Allow All Origins (Cloud Mode)
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
        proxyRes.headers['Access-Control-Allow-Origin'] = '*';
    }
};

app.use('/api', createProxyMiddleware(proxyOptions));

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
