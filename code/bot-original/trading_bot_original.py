#!/usr/bin/env python3
"""
Trading Bot Original - Versao com REST (Antes da Otimizacao)
Operacao Scalper de Baixa Latencia - Binance
"""

import time
import json
import logging
from datetime import datetime
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuracao de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OriginalTradingBot:
    """
    Bot de trading original - usa apenas REST com conexoes independentes
    Cada chamada cria uma nova conexao TCP + TLS
    """
    
    def __init__(self):
        # Configuracoes da API Binance
        self.base_url = "https://api.binance.com/api/v3"
        self.api_key = "SUA_API_KEY_AQUI"  # Substituir pela chave real
        self.api_secret = "SUA_API_SECRET_AQUI"  # Substituir pela chave real
        
        # Sessao HTTP sem keep-alive otimizado
        self.session = self._create_session()
        
        # Variaveis de estado
        self.current_price = None
        self.balance = None
        self.rsi = None
        
        # Contadores para diagnostico
        self.cycle_count = 0
        self.total_latency = 0
        
    def _create_session(self):
        """Cria sessao HTTP com retry (sem keep-alive otimizado)"""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session
    
    def get_price_rest(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """
        Obtem preco atual via REST
        Cada chamada: DNS + TCP handshake + TLS handshake + Request + Response
        """
        try:
            # Cada chamada REST cria uma nova conexao TCP
            # Overhead: ~50-200ms por chamada
            start_time = time.time()
            
            response = self.session.get(
                f"{self.base_url}/ticker/price",
                params={"symbol": symbol}
            )
            response.raise_for_status()
            
            data = response.json()
            price = float(data['price'])
            
            elapsed = (time.time() - start_time) * 1000  # em ms
            logger.debug(f"Preco obtido: ${price:.2f} (latencia: {elapsed:.2f}ms)")
            
            return price
            
        except Exception as e:
            logger.error(f"Erro ao obter preco: {e}")
            return None
    
    def get_balance_rest(self) -> Optional[Dict]:
        """
        Obtem saldo da conta via REST
        Nova conexao TCP + TLS a cada chamada
        """
        try:
            start_time = time.time()
            
            headers = {"X-MBX-APIKEY": self.api_key}
            response = self.session.get(
                f"{self.base_url}/account",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            balance = data.get('balances', [])
            
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"Saldo obtido (latencia: {elapsed:.2f}ms)")
            
            return balance
            
        except Exception as e:
            logger.error(f"Erro ao obter saldo: {e}")
            return None
    
    def get_rsi_rest(self, symbol: str = "BTCUSDT") -> Optional[float]:
        """
        Obtem dados historicos e calcula RSI via REST
        Nova conexao TCP + TLS a cada chamada
        """
        try:
            start_time = time.time()
            
            response = self.session.get(
                f"{self.base_url}/klines",
                params={
                    "symbol": symbol,
                    "interval": "1m",
                    "limit": 14  # Periodo para RSI
                }
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Calculo simplificado do RSI
            closes = [float(candle[4]) for candle in data]
            rsi = self._calculate_rsi(closes)
            
            elapsed = (time.time() - start_time) * 1000
            logger.debug(f"RSI calculado: {rsi:.2f} (latencia: {elapsed:.2f}ms)")
            
            return rsi
            
        except Exception as e:
            logger.error(f"Erro ao calcular RSI: {e}")
            return None
    
    def _calculate_rsi(self, prices: list) -> float:
        """Calcula RSI simplificado"""
        if len(prices) < 2:
            return 50.0
        
        gains = 0
        losses = 0
        
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff > 0:
                gains += diff
            else:
                losses += abs(diff)
        
        if losses == 0:
            return 100.0
        
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def send_order_rest(self, side: str, quantity: float) -> Optional[Dict]:
        """
        Envia ordem via REST
        Nova conexao TCP + TLS para cada ordem
        """
        try:
            start_time = time.time()
            
            if self.current_price is None:
                logger.error("Preco nao disponivel para enviar ordem")
                return None
            
            # Preco limit: 0.1% acima/abaixo do preco atual
            price = self.current_price * (1.001 if side.upper() == "BUY" else 0.999)
            
            headers = {"X-MBX-APIKEY": self.api_key}
            payload = {
                "symbol": "BTCUSDT",
                "side": side.upper(),
                "type": "LIMIT",
                "price": f"{price:.2f}",
                "quantity": f"{quantity:.8f}",
                "timeInForce": "GTC"
            }
            
            response = self.session.post(
                f"{self.base_url}/order",
                headers=headers,
                data=payload
            )
            response.raise_for_status()
            
            order = response.json()
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"Ordem enviada: {side} {quantity} BTC (latencia: {elapsed:.2f}ms)")
            
            return order
            
        except Exception as e:
            logger.error(f"Erro ao enviar ordem: {e}")
            return None
    
    def evaluate_strategy(self) -> Optional[Dict]:
        """
        Avalia estrategia de scalping
        """
        if self.rsi is None:
            return None
        
        # Estrategia simples: compra se RSI < 30, vende se RSI > 70
        if self.rsi < 30:
            return {"side": "BUY", "quantity": 0.001}
        elif self.rsi > 70:
            return {"side": "SELL", "quantity": 0.001}
        
        return None
    
    def trading_cycle(self):
        """
        Ciclo completo de trading
        Cada ciclo faz multiplas chamadas REST sequenciais
        """
        cycle_start = time.time()
        self.cycle_count += 1
        
        logger.info(f"=== CICLO {self.cycle_count} ===")
        
        # 1. Obtem preco (REST) - Nova conexao
        self.current_price = self.get_price_rest()
        if self.current_price is None:
            return
        
        # 2. Obtem saldo (REST) - Nova conexao
        self.balance = self.get_balance_rest()
        if self.balance is None:
            return
        
        # 3. Obtem RSI (REST) - Nova conexao
        self.rsi = self.get_rsi_rest()
        if self.rsi is None:
            return
        
        # 4. Avalia estrategia (local, sem rede)
        decision = self.evaluate_strategy()
        
        # 5. Executa ordem se necessario (REST) - Nova conexao
        if decision:
            order = self.send_order_rest(decision['side'], decision['quantity'])
            if order:
                logger.info(f"Ordem executada com sucesso: {order}")
        
        # Calcula latencia total do ciclo
        cycle_latency = (time.time() - cycle_start) * 1000
        self.total_latency += cycle_latency
        
        logger.info(f"Latencia total do ciclo: {cycle_latency:.2f}ms")
        
        # Estatisticas
        avg_latency = self.total_latency / self.cycle_count
        logger.info(f"Latencia media: {avg_latency:.2f}ms")
        logger.info("============================\n")
    
    def run(self, cycles: int = 10):
        """
        Executa o bot por N ciclos
        """
        logger.info(f"Iniciando Trading Bot Original - {cycles} ciclos")
        logger.info("ATENCAO: Cada chamada REST cria uma nova conexao TCP + TLS")
        
        for i in range(cycles):
            self.trading_cycle()
            time.sleep(0.5)  # Aguarda 500ms entre ciclos
        
        # Relatorio final
        avg_latency = self.total_latency / self.cycle_count
        logger.info("========== RELATORIO FINAL ==========")
        logger.info(f"Total de ciclos: {self.cycle_count}")
        logger.info(f"Latencia media: {avg_latency:.2f}ms")
        logger.info(f"Latencia total: {self.total_latency:.2f}ms")
        logger.info("=====================================")


if __name__ == "__main__":
    bot = OriginalTradingBot()
    bot.run(cycles=5)