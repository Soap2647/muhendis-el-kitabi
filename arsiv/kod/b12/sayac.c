#include <stdio.h>

typedef long long ll;

ll tek_dongu(ll n) {
    ll say = 0;
    for (ll i = 0; i < n; i++)
        say++;
    return say;
}

ll ic_ice(ll n) {
    ll say = 0;
    for (ll i = 0; i < n; i++)
        for (ll j = 0; j < n; j++)
            say++;
    return say;
}

ll bagimli(ll n) {
    ll say = 0;
    for (ll i = 0; i < n; i++)
        for (ll j = 0; j < i; j++)
            say++;
    return say;
}

ll log_dongu(ll n) {
    ll say = 0;
    for (ll i = 1; i < n; i *= 2)
        say++;
    return say;
}

ll harmonik(ll n) {
    ll say = 0;
    for (ll i = 1; i <= n; i++)
        for (ll j = 1; j <= n; j += i)
            say++;
    return say;
}

int main(void) {
    ll boyut[] = {10, 100, 1000};
    for (int k = 0; k < 3; k++) {
        ll n = boyut[k];
        printf("n=%5lld tek=%5lld ic=%8lld bagimli=%7lld log=%3lld harm=%6lld\n",
               n, tek_dongu(n), ic_ice(n), bagimli(n), log_dongu(n),
               harmonik(n));
    }
    return 0;
}
