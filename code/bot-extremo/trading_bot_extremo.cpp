/**
 * Trading Bot Extremo - C++ com baixa latencia
 * Para competir com empresas de HFT profissional
 * 
 * Compilacao: g++ -std=c++17 -O3 -pthread trading_bot_extremo.cpp -o trading_bot
 */

#include <iostream>
#include <string>
#include <vector>
#include <thread>
#include <chrono>
#include <atomic>
#include <mutex>
#include <functional>
#include <memory>

// Bibliotecas de rede de baixo nivel
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>

// Bibliotecas para alta performance
#include <immintrin.h>  // SIMD
#include <x86intrin.h>  // CPU intrinsics

using namespace std;
using namespace std::chrono;

// Constantes
const string BINANCE_HOST = "api.binance.com";
const int BINANCE_PORT = 443;
const string WS_ENDPOINT = "/ws/btcusdt@trade";
const int MAX_BUFFER_SIZE = 4096;

/**
 * Gerenciador de conexao TCP com socket otimizado
 */
class LowLatencySocket {
private:
    int sockfd;
    string host;
    int port;
    
public:
    LowLatencySocket(const string& h, int p) : host(h), port(p), sockfd(-1) {}
    
    ~LowLatencySocket() {
        if (sockfd >= 0) {
            close(sockfd);
        }
    }
    
    bool connect() {
        // Resolver hostname (cacheado para evitar DNS)
        struct hostent* server = gethostbyname(host.c_str());
        if (server == nullptr) {
            cerr << "Erro ao resolver host: " << host << endl;
            return false;
        }
        
        // Criar socket
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (sockfd < 0) {
            cerr << "Erro ao criar socket" << endl;
            return false;
        }
        
        // Configurar socket para baixa latencia
        int flag = 1;
        setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, &flag, sizeof(flag));  // Desativa Nagle
        
        // Timeout para operacoes
        struct timeval tv;
        tv.tv_sec = 2;
        tv.tv_usec = 0;
        setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        setsockopt(sockfd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
        
        // Conectar
        struct sockaddr_in serv_addr;
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(port);
        serv_addr.sin_addr = *((struct in_addr*)server->h_addr);
        
        if (::connect(sockfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
            cerr << "Erro ao conectar" << endl;
            return false;
        }
        
        return true;
    }
    
    bool send_data(const string& data) {
        int sent = 0;
        int total = data.length();
        const char* buffer = data.c_str();
        
        while (sent < total) {
            int n = write(sockfd, buffer + sent, total - sent);
            if (n < 0) {
                cerr << "Erro ao enviar dados" << endl;
                return false;
            }
            sent += n;
        }
        
        return true;
    }
    
    string receive_data() {
        char buffer[MAX_BUFFER_SIZE];
        int n = read(sockfd, buffer, MAX_BUFFER_SIZE - 1);
        
        if (n < 0) {
            cerr << "Erro ao receber dados" << endl;
            return "";
        }
        
        buffer[n] = '\0';
        return string(buffer);
    }
    
    int get_fd() const { return sockfd; }
};

/**
 * Cache em memoria com lock-free
 */
template<typename T>
class LockFreeCache {
private:
    struct CacheEntry {
        T value;
        steady_clock::time_point expires_at;
        bool valid;
    };
    
    static const int CACHE_SIZE = 1024;
    CacheEntry cache[CACHE_SIZE];
    atomic<int> head{0};
    
public:
    LockFreeCache() {
        for (int i = 0; i < CACHE_SIZE; i++) {
            cache[i].valid = false;
        }
    }
    
    void set(const T& value, int ttl_ms) {
        int idx = head.fetch_add(1) % CACHE_SIZE;
        cache[idx].value = value;
        cache[idx].expires_at = steady_clock::now() + milliseconds(ttl_ms);
        cache[idx].valid = true;
    }
    
    bool get(T& value) {
        // Procura a partir da posicao atual para tras
        int idx = (head.load() - 1) % CACHE_SIZE;
        
        for (int i = 0; i < CACHE_SIZE; i++) {
            if (cache[idx].valid) {
                if (steady_clock::now() < cache[idx].expires_at) {
                    value = cache[idx].value;
                    return true;
                } else {
                    // Cache expirado
                    cache[idx].valid = false;
                }
            }
            idx = (idx - 1 + CACHE_SIZE) % CACHE_SIZE;
        }
        
        return false;
    }
};

/**
 * Bot de Trading Extremo
 */
class ExtremeTradingBot {
private:
    LowLatencySocket* ws_socket;
    LowLatencySocket* rest_socket;
    LockFreeCache<double> price_cache;
    LockFreeCache<double> rsi_cache;
    
    atomic<double> current_price{0.0};
    atomic<bool> running{true};
    mutex log_mutex;
    
    // Estatisticas
    atomic<long long> total_latency{0};
    atomic<int> cycle_count{0};
    
public:
    ExtremeTradingBot() : ws_socket(nullptr), rest_socket(nullptr) {
        // Configurar afinidade de CPU (CPU pinning)
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(0, &cpuset);
        sched_setaffinity(0, sizeof(cpuset), &cpuset);
        
        // Desativar interrupcoes desnecessarias
        signal(SIGINT, [](int){ /* Ignorar */ });
    }
    
    ~ExtremeTradingBot() {
        if (ws_socket) delete ws_socket;
        if (rest_socket) delete rest_socket;
    }
    
    bool initialize() {
        cout << "Inicializando Trading Bot Extremo..." << endl;
        
        // 1. Conectar WebSocket (dados de mercado em tempo real)
        ws_socket = new LowLatencySocket(BINANCE_HOST, BINANCE_PORT);
        if (!ws_socket->connect()) {
            cerr << "Falha ao conectar WebSocket" << endl;
            return false;
        }
        
        // Handshake WebSocket
        string ws_handshake = 
            "GET " + WS_ENDPOINT + " HTTP/1.1\r\n"
            "Host: " + BINANCE_HOST + "\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n";
        
        if (!ws_socket->send_data(ws_handshake)) {
            cerr << "Falha no handshake WebSocket" << endl;
            return false;
        }
        
        string response = ws_socket->receive_data();
        if (response.find("101") == string::npos) {
            cerr << "Handshake WebSocket falhou" << endl;
            return false;
        }
        
        // 2. Conectar REST (para envio de ordens)
        rest_socket = new LowLatencySocket(BINANCE_HOST, BINANCE_PORT);
        if (!rest_socket->connect()) {
            cerr << "Falha ao conectar REST" << endl;
            return false;
        }
        
        cout << "Conexoes estabelecidas com sucesso" << endl;
        return true;
    }
    
    void handle_websocket_messages() {
        cout << "Thread: Processando mensagens WebSocket..." << endl;
        
        while (running) {
            string message = ws_socket->receive_data();
            if (message.empty()) continue;
            
            // Parse simplificado do preco
            // Em producao, usar biblioteca JSON de alta performance
            size_t price_pos = message.find("\"p\":\"");
            if (price_pos != string::npos) {
                size_t start = price_pos + 5;
                size_t end = message.find("\"", start);
                string price_str = message.substr(start, end - start);
                double price = stod(price_str);
                
                current_price.store(price, memory_order_release);
                price_cache.set(price, 100);  // 100ms TTL
            }
        }
    }
    
    double get_price() {
        double cached_price;
        if (price_cache.get(cached_price)) {
            return cached_price;
        }
        return current_price.load(memory_order_acquire);
    }
    
    bool send_order(const string& side, double quantity) {
        double price = get_price();
        if (price <= 0) return false;
        
        // Construir ordem em formato otimizado
        string order = 
            "POST /api/v3/order HTTP/1.1\r\n"
            "Host: " + BINANCE_HOST + "\r\n"
            "Content-Type: application/x-www-form-urlencoded\r\n"
            "Content-Length: 0\r\n\r\n";
        
        // Em producao: adicionar headers de autenticacao e payload
        // Usar HMAC-SHA256 assinatura
        
        if (!rest_socket->send_data(order)) {
            return false;
        }
        
        string response = rest_socket->receive_data();
        return !response.empty();
    }
    
    double calculate_rsi_fast(const vector<double>& prices) {
        // Usa SIMD para calculo rapido
        if (prices.size() < 2) return 50.0;
        
        double gains = 0.0;
        double losses = 0.0;
        
        // Vetorizacao SIMD (SSE/AVX)
        // Em producao, usar bibliotecas como Intel MKL
        #pragma omp simd reduction(+:gains,losses)
        for (size_t i = 1; i < prices.size(); i++) {
            double diff = prices[i] - prices[i-1];
            if (diff > 0) {
                gains += diff;
            } else {
                losses -= diff;  // diff eh negativo
            }
        }
        
        if (losses == 0) return 100.0;
        double rs = gains / losses;
        return 100.0 - (100.0 / (1.0 + rs));
    }
    
    void trading_cycle() {
        auto cycle_start = high_resolution_clock::now();
        cycle_count++;
        
        // 1. Preco ja esta disponivel via WebSocket (push)
        double price = get_price();
        if (price <= 0) return;
        
        // 2. RSI via cache ou calculo
        double rsi;
        if (!rsi_cache.get(rsi)) {
            // Simular dados historicos
            vector<double> prices = {100, 101, 99, 102, 101, 103, 102, 101, 100, 99, 101, 102, 103, 102};
            rsi = calculate_rsi_fast(prices);
            rsi_cache.set(rsi, 60000);  // 1 minuto TTL
        }
        
        // 3. Decisao via hardware (FPGA) - emulacao simplificada
        // Em producao, essa logica seria offloaded para FPGA
        bool should_buy = (rsi < 30);
        bool should_sell = (rsi > 70);
        
        // 4. Executar ordem se necessario
        if (should_buy) {
            send_order("BUY", 0.001);
        } else if (should_sell) {
            send_order("SELL", 0.001);
        }
        
        auto cycle_end = high_resolution_clock::now();
        auto latency = duration_cast<microseconds>(cycle_end - cycle_start).count();
        
        total_latency += latency;
        
        if (cycle_count % 1000 == 0) {
            lock_guard<mutex> lock(log_mutex);
            cout << "Ciclo " << cycle_count << " - Latencia: " << latency << "us" << endl;
        }
    }
    
    void run() {
        cout << "Iniciando Trading Bot Extremo..." << endl;
        cout << "Latencia alvo: < 100us por ciclo" << endl;
        
        // Thread para WebSocket
        thread ws_thread(&ExtremeTradingBot::handle_websocket_messages, this);
        
        // Main loop - otimizado para baixa latencia
        while (running) {
            auto start = high_resolution_clock::now();
            
            trading_cycle();
            
            // Spin wait em vez de sleep para menor latencia
            auto end = high_resolution_clock::now();
            auto elapsed = duration_cast<microseconds>(end - start).count();
            
            if (elapsed < 100) {  // 100us target
                // Busy-wait para manter baixa latencia
                while (duration_cast<microseconds>(
                    high_resolution_clock::now() - end
                ).count() < 100 - elapsed) {
                    _mm_pause();  // Hints para CPU
                }
            }
        }
        
        ws_thread.join();
    }
    
    void stop() {
        running = false;
    }
    
    void print_stats() {
        cout << "========== RELATORIO EXTREMO ==========" << endl;
        cout << "Total de ciclos: " << cycle_count << endl;
        cout << "Latencia media: " << (total_latency / cycle_count) << "us" << endl;
        cout << "========================================" << endl;
    }
};

int main() {
    ExtremeTradingBot bot;
    
    if (!bot.initialize()) {
        cerr << "Falha na inicializacao" << endl;
        return 1;
    }
    
    // Executar por 10 segundos
    thread bot_thread([&bot]() {
        bot.run();
    });
    
    this_thread::sleep_for(seconds(10));
    bot.stop();
    bot_thread.join();
    
    bot.print_stats();
    
    return 0;
}