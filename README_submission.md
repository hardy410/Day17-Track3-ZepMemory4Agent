# Lab 17 Submission

## Nhan xet chinh

Trong bo test nay, long-term memory la layer quan trong nhat: no quyet dinh E02, E03, E08 va E09, dong thoi cung cap preference Python cho case mixed E07. Day la layer co do phu rong nhat va kiem tra ca cross-session recall, open loop, recency lan user isolation.

Zep Context Block co loi the la tu dong tong hop user graph, lien ket facts qua nhieu thread va giu provenance/validity de xu ly xung dot. Doi lai, no phu thuoc dich vu managed, co latency mang va co the tra context dai. Redis + Qdrant cho quyen kiem soat chi phi, TTL, schema va retrieval pipeline, nhung doi hoi tu xay extraction, namespace, conflict resolution, deletion va monitoring.

Guardrail chong memory poisoning gom: chi durable-write khi user da opt-in; allow-list memory type; tach namespace theo user/project; luu source, timestamp, confidence va validity; yeu cau review voi preference co tac dong cao; khong cho retrieved memory ghi de system/policy context. Fact moi mau thuan phai duoc doi chieu scope va provenance truoc khi supersede fact cu.

## Phan tich benchmark

Student benchmark dat 11/11, hit rate 100%, nen khong co layer nao co hit rate thap hon. Long-term ton nhieu context nhat: E02 retrieve 1.570 token, cao nhat bo test; trung binh long-term la 1.341,8 token. E07 can ket hop long-term de lay preference Python cua Minh va semantic memory de lay quy tac Idempotency-Key.

Average token reduction la 14,19%. Co the giam token ma khong giam hit rate bang cach trim cac fact/context lap lai, ranking marker-bearing evidence len dau va ap dung budget theo layer. Khong nen coi no-memory reduction cao la tot, vi baseline chi dat 2/11.

E08 cho thay recency phai di kem scope: BLUEBIRD-42 dung TypeScript/NestJS, trong khi Python van dung cho ORCHID-27. E10 cho thay compaction khong chi tom tat hoi thoai; durable note van giu `REVIEW-DEADLINE-1600`, Friday va 16:00 sau khi raw turn cu bi loai.
