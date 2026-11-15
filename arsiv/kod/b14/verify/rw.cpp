#include <algorithm>
#include <cstdio>
#include <vector>

int main() {
    std::vector<int> v = {1, 2, 2, 2, 3};
    auto lb = std::lower_bound(v.begin(), v.end(), 2) - v.begin();
    auto ub = std::upper_bound(v.begin(), v.end(), 2) - v.begin();
    std::printf("lower_bound(2)=%ld upper_bound(2)=%ld\n", (long)lb, (long)ub);
    std::printf("binary_search(2)=%d\n",
                (int)std::binary_search(v.begin(), v.end(), 2));
    return 0;
}
