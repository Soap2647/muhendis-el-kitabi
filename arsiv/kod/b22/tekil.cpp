// tekil.cpp: Meyers singleton ve es zamanli erisim (C++11 ve sonrasi)
#include <atomic>
#include <iostream>
#include <thread>
#include <vector>

std::atomic<int> kurulum{0};

class Yapilandirma {
public:
    static Yapilandirma& al() {
        static Yapilandirma tek;       // ilk cagrida bir kez kurulur
        return tek;
    }
    int mod = 0;

private:
    Yapilandirma() { ++kurulum; }
};

int main() {
    std::atomic<const void*> ilk{nullptr};
    std::atomic<bool> tutarli{true};
    std::vector<std::thread> is;
    for (int t = 0; t < 8; ++t) {
        is.emplace_back([&] {
            for (int k = 0; k < 1000; ++k) {
                const void* p = &Yapilandirma::al();
                const void* beklenen = nullptr;
                if (!ilk.compare_exchange_strong(beklenen, p) &&
                    beklenen != p)
                    tutarli = false;
            }
        });
    }
    for (auto& th : is) th.join();
    std::cout << "kurulum sayisi: " << kurulum.load() << "\n";
    std::cout << "ayni ornek: " << (tutarli.load() ? "true" : "false")
              << "\n";
}
