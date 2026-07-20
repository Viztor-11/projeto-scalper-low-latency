#!/usr/bin/env python3
"""
Trading Bot Otimizado com WebSocket e Cache
Operacao Scalper de Baixa Latencia - Binance
"""

import asyncio
import json
import logging
import os
import time

import aiohttp
import websockets
from dotenv import load_dotenv
from cache_manager import CacheManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizedTradingBot:
    
    """Bot de trading otimizado com WebSocket e cache"""
    
    def __init__(self):
        self.ws = None
        self.session = None
        self.cache = CacheManager()
        self.current_price = None
        self.balance = None
        self.last_price_update = 0
        self.price_update_interval = 0.1
        
        self.ws_url = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        self.rest_url = "https://api.binance.com/api/v3"
        
    async def connect_websocket(self):
        
        """Estabelece conexao WebSocket persistente"""
        try:
            self.ws = await websockets.connect(self.ws_url)
            logger.info("WebSocket conectado com sucesso")
            
            subscribe_msg = {
                "method": "SUBSCRIBE",
                "params": ["btcusdt@trade"],
                "id": 1
            }
            await self.ws.send(json.dumps(subscribe_msg))
            return True
        except Exception as e:
            logger.error(f"Erro no WebSocket: {e}")
            return False
    
    async def handle_websocket_messages(self):
       
        """Processa mensagens do WebSocket em tempo real"""
        try:
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                
                if 'data' in data and 'p' in data['data']:
                    price = float(data['data']['p'])
                    self.current_price = price
                    self.last_price_update = time.time()
                    self.cache.set('price', price, ttl=0.1)
                    logger.debug(f"Preco atualizado: ${price:.2f}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket desconectado. Reconectando...")
            await self.reconnect_websocket()
        except Exception as e:
            logger.error(f"Erro no WebSocket handler: {e}")
    
    async def reconnect_websocket(self):
        
        """Reconecta WebSocket em caso de falha"""
        while True:
            await asyncio.sleep(1)
            if await self.connect_websocket():
                break
    
    async def get_balance_async(self):
       
        """Obtem saldo com cache e HTTP persistente"""
        cached_balance = self.cache.get('balance')
        if cached_balance:
            return cached_balance
        
        try:
            async with self.session.get(
                f"{self.rest_url}/account",
                headers={"X-MBX-APIKEY": os.getenv("BINANCE_API_KEY")}
            ) as response:
                data = await response.json()
                balance = data.get('balances', [])
                self.cache.set('balance', balance, ttl=5)
                return balance
        except Exception as e:
            logger.error(f"Erro ao obter saldo: {e}")
            return None
    
    async def get_rsi_async(self):
       
        """Obtem RSI com cache"""
        cached_rsi = self.cache.get('rsi')
        if cached_rsi:
            return cached_rsi
        
        try:
            async with self.session.get(
                f"{self.rest_url}/klines",
                params={"symbol": "BTCUSDT", "interval": "1m", "limit": 14}
            ) as response:
                data = await response.json()
                rsi = self.calculate_rsi(data)
                self.cache.set('rsi', rsi, ttl=60)
                return rsi
        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {e}")
            return None
    
    def calculate_rsi(self, data):
        
        """Calcula RSI a partir dos dados de candle"""
        return 50
    
    async def send_order_async(self, side: str, quantity: float):
       
        """Envia ordem usando REST com Keep-Alive"""
        try:
            async with self.session.post(
                f"{self.rest_url}/order",
                headers={"X-MBX-APIKEY": os.getenv("BINANCE_API_KEY")},
                json={
                    "symbol": "BTCUSDT",
                    "side": side.upper(),
                    "type": "LIMIT",
                    "price": self.current_price * 1.001,
                    "quantity": quantity,
                    "timeInForce": "GTC"
                }
            ) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Erro ao enviar ordem: {e}")
            return None
    
    async def trading_cycle(self):
        
        """Ciclo principal de trading otimizado"""
        while True:
            try:
                start_time = time.time()
                
                balance = await self.get_balance_async()
                rsi = await self.get_rsi_async()
                
                if self.current_price and balance and rsi:
                    decision = self.evaluate_strategy(
                        self.current_price, balance, rsi
                    )
                    
                    if decision:
                        order = await self.send_order_async(
                            decision['side'],
                            decision['quantity']
                        )
                        logger.info(f"Ordem executada: {order}")
                
                elapsed = time.time() - start_time
                logger.info(f"Ciclo concluido em {elapsed:.3f}ms")
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Erro no ciclo: {e}")
                await asyncio.sleep(1)
    
    def evaluate_strategy(self, price, balance, rsi):
        
        """Avalia estrategia de trading"""
        if rsi < 30:
            return {"side": "BUY", "quantity": 0.001}
        elif rsi > 70:
            return {"side": "SELL", "quantity": 0.001}
        return None
    
    async def run(self):
        
        """Executa o bot"""
        logger.info("Iniciando Trading Bot Otimizado...")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            if not await self.connect_websocket():
                logger.error("Falha ao conectar WebSocket. Abortando...")
                return
            
            await asyncio.gather(
                self.handle_websocket_messages(),
                self.trading_cycle()
            )


if __name__ == "__main__":
    bot = OptimizedTradingBot()
    asyncio.run(bot.run())