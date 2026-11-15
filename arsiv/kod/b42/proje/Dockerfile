# Çok aşamalı derleme: araç zinciri yalnızca birinci aşamada.
FROM gcc:13 AS derle
WORKDIR /src
COPY crc32_arac.c .
RUN mkdir /cikti && \
    gcc -O2 -Wall -Wextra -Werror -std=c11 -static \
        crc32_arac.c -o /cikti/crc32_arac

# Çalışma aşaması: boş imaj. İçinde kabuk, paket yöneticisi yok.
FROM scratch
COPY --from=derle /cikti/crc32_arac /crc32_arac
USER 65532:65532
ENTRYPOINT ["/crc32_arac"]
