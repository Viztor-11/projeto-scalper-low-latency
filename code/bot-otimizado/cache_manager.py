"""
Gerenciador de Cache em Memoria para Baixa Latencia
"""

import time
from typing import Any, Optional
from threading import Lock


class CacheManager:
    """Cache em memoria com TTL e thread-safe"""
    
    def __init__(self):
        self._cache = {}
        self._lock = Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'total_get': 0,
            'total_set': 0
        }
    
    def set(self, key: str, value: Any, ttl: float = 5.0):
        
        """Armazena valor com TTL em segundos"""
        with self._lock:
            expires_at = time.time() + ttl if ttl > 0 else float('inf')
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
            self._stats['total_set'] += 1
            
            if self._stats['total_set'] % 1000 == 0:
                self._cleanup()
    
    def get(self, key: str) -> Optional[Any]:
        
        """Obtem valor do cache se ainda nao expirou"""
        self._stats['total_get'] += 1
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            if time.time() > entry['expires_at']:
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            self._stats['hits'] += 1
            return entry['value']
    
    def delete(self, key: str):
        
        """Remove uma chave especifica do cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        
        """Limpa todo o cache"""
        with self._lock:
            self._cache.clear()
    
    def _cleanup(self):
        
        """Remove entradas expiradas"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get_stats(self) -> dict:
        
        """Retorna estatisticas do cache"""
        hit_rate = 0
        if self._stats['total_get'] > 0:
            hit_rate = self._stats['hits'] / self._stats['total_get']
        
        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': f"{hit_rate * 100:.2f}%",
            'total_get': self._stats['total_get'],
            'total_set': self._stats['total_set'],
            'cache_size': len(self._cache)
        }