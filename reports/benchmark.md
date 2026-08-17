# Lab 17 Benchmark Report

- Implementation: `student`
- Kind: `practice`
- Cases: **11**
- Passed: **11/11**
- Evidence hit rate: **100.0%**
- Average retrieval latency: **888.8 ms**
- Average token reduction vs full source context: **19.1%**

| Case | Layer | Pass | Latency ms | Retrieved tokens | Token reduction | Missing / Error |
| --- | --- | --- | ---: | ---: | ---: | --- |
| E01 | short_term | PASS | 0.1 | 133 | 0.0% |  |
| E06 | semantic | PASS | 640.1 | 53 | 88.4% |  |
| E09 | long_term | PASS | 1353.6 | 816 | 0.0% |  |
| E10 | short_term | PASS | 0.2 | 195 | 0.0% |  |
| E02 | long_term | PASS | 1724.0 | 1567 | 0.0% |  |
| E03 | long_term | PASS | 1831.5 | 1537 | 0.0% |  |
| E04 | episodic | PASS | 303.5 | 233 | 0.0% |  |
| E05 | episodic | PASS | 312.1 | 252 | 0.0% |  |
| E07 | mixed | PASS | 1863.2 | 390 | 31.0% |  |
| E11 | semantic | PASS | 223.7 | 52 | 90.8% |  |
| E08 | long_term | PASS | 1524.3 | 1501 | 0.0% |  |

## Evidence excerpts

### E01 - short_term

`<RECENT_TURNS> user: Ten du an ca nhan cua toi la ORCHID-27. Toi thich Python va khong thich Java. Khi giai thich code, hay dung vi du ngan. assistant: Da hieu: demo ca nhan ORCHID-27, uu tien Python, tranh Java, vi du ngan. user: Toi dang hoc async/await va hay nham coroutine voi Task. Neu sau nay gap chu de nay, hay giai thich bang timeline. assistant: Toi se uu tien timeline khi giai thich coroutine va Task. user: TODO: hoan thanh benchmark report truoc thu Sau luc 16:00. Day la open loop LAB-REPORT-1600. </RECENT_TURNS>`

### E06 - semantic

`EPISODE: For POST /payments, every retryable request MUST send the same Idempotency-Key. Retry only HTTP 429 or transient 5xx errors, use exponential-backoff, and stop after max-3-retries. Marker: PAYMENT-RULE-3.`

### E09 - long_term

`<USER_SUMMARY> Lan's project is LOTUS-88. They prioritize Java and Spring Boot for backend examples and do not use Python in the backend. </USER_SUMMARY>  <EPISODES> Episodes are source message or document excerpts shown in selection order.   - Created At: 2026-08-01 11:00:20     Source: message     Content: Lab Assistant (assistant): Da hieu: LOTUS-88, Java + Spring Boot cho backend examples.   - Created At: 2026-08-01 11:00:00     Source: message     Content: [user] {   "user_id": "lan-lab17",   "first_name": "Lan",   "last_name": "Tran",   "user_alias": "Lan Tran" }: Toi la Lan. Du an cua toi la LOTUS-88. Toi uu tien Java va Spring Boot, va khong dung Python trong vi du backend.   - Creat`

### E10 - short_term

`<SESSION_SUMMARY> user: Constraint: REVIEW-DEADLINE-1600 - project review is Friday at 16:00 and must not be forgotten. | assistant: Acknowledged review constraint. | user: Filler turn 1 about UI spacing. | assistant: Filler answer 1. | user: Filler turn 2 about naming. | assistant: Filler answer 2. | user: Filler turn 3 about logging. | assistant: Filler answer 3. </SESSION_SUMMARY> <DURABLE_NOTES> - user: Constraint: REVIEW-DEADLINE-1600 - project review is Friday at 16:00 and must not be forgotten. - assistant: Acknowledged review constraint. </DURABLE_NOTES> <RECENT_TURNS> user: Filler turn 4 about tests. assistant: Filler answer 4. user: Filler turn 5 about docs. assistant: Filler answe`

### E02 - long_term

`<USER_SUMMARY> Minh's personal project is named ORCHID-27, for which he prefers Python. For the company project BLUEBIRD-42, the backend must use TypeScript with NestJS, and Python is not to be used for this project. The user is learning about async/await and often confuses coroutines with Tasks. Minh has a deadline to complete a benchmark report by Saturday at 16:00, referred to as open loop LAB-REPORT-1600. He is currently debugging async HTTP and has tried increasing the timeout to 60s without success. Minh resolved a connection churn issue related to ASYNC-FIX-20 by reusing an aiohttp ClientSession and setting concurrency to 20, noting that increasing the timeout was ineffective.  Minh p`

### E03 - long_term

`<USER_SUMMARY> Minh's personal project is named ORCHID-27, for which he prefers Python. For the company project BLUEBIRD-42, the backend must use TypeScript with NestJS, and Python is not to be used for this project. The user is learning about async/await and often confuses coroutines with Tasks. Minh has a deadline to complete a benchmark report by Saturday at 16:00, referred to as open loop LAB-REPORT-1600. He is currently debugging async HTTP and has tried increasing the timeout to 60s without success. Minh resolved a connection churn issue related to ASYNC-FIX-20 by reusing an aiohttp ClientSession and setting concurrency to 20, noting that increasing the timeout was ineffective.  Minh p`

### E04 - episodic

`EPISODE: Cap nhat moi: voi du an cong ty BLUEBIRD-42, backend bat buoc dung TypeScript voi NestJS; khong dung Python cho backend du an nay. Preference Python van dung cho demo ca nhan ORCHI EPISODE: Hom nay toi debug async HTTP. Toi da thu tang timeout len 60s nhung van fail. EPISODE: Cach hieu qua la reuse aiohttp ClientSession va dat concurrency=20. Reflection: loi chinh la connection churn, khong phai timeout threshold. Ma su co ASYNC-FIX-20. EPISODE: Da ghi nhan trajectory: increase timeout khong hieu qua; ClientSession + concurrency=20 giai quyet connection churn. EPISODE: Ten du an ca nhan cua toi la ORCHID-27. Toi thich Python va khong thich Java. Khi giai thich code, hay dung vi du n`

### E05 - episodic

`EPISODE: Cap nhat moi: voi du an cong ty BLUEBIRD-42, backend bat buoc dung TypeScript voi NestJS; khong dung Python cho backend du an nay. Preference Python van dung cho demo ca nhan ORCHI EPISODE: Hom nay toi debug async HTTP. Toi da thu tang timeout len 60s nhung van fail. EPISODE: Hay kiem tra connection pool, lifecycle cua client va concurrency. EPISODE: Cach hieu qua la reuse aiohttp ClientSession va dat concurrency=20. Reflection: loi chinh la connection churn, khong phai timeout threshold. Ma su co ASYNC-FIX-20. EPISODE: Da ghi nhan trajectory: increase timeout khong hieu qua; ClientSession + concurrency=20 giai quyet connection churn. EPISODE: Ten du an ca nhan cua toi la ORCHID-27.`

### E07 - mixed

`<LONG_TERM> <USER_SUMMARY> Minh's personal project is named ORCHID-27, for which he prefers Python. For the company project BLUEBIRD-42, the backend must use TypeScript with NestJS, and Python is not to be used for this project. The user is learning about async/await and often confuses coroutines with Tasks. Minh has a deadline to complete a benchmark report by Saturday at 16:00, referred to as open loop LAB-REPORT-1600. He is currently debugging async HTTP and has tried increasing the timeout to 60s without success. Minh resolved a connection churn issue related to ASYNC-FIX-20 by reusing an aiohttp ClientSession and setting concurrency to 20, noting that increasing the timeout was ineffect`

### E11 - semantic

`EPISODE: When async HTTP calls time out, inspect connection pooling, downstream saturation and concurrency before increasing timeout. Reuse a long-lived client session where possible. Marker: CONN-POOL-FIRST.`

### E08 - long_term

`<USER_SUMMARY> Minh's personal project is named ORCHID-27, for which he prefers Python. For the company project BLUEBIRD-42, the backend must use TypeScript with NestJS, and Python is not to be used for this project. The user is learning about async/await and often confuses coroutines with Tasks. Minh has a deadline to complete a benchmark report by Saturday at 16:00, referred to as open loop LAB-REPORT-1600. He is currently debugging async HTTP and has tried increasing the timeout to 60s without success. Minh resolved a connection churn issue related to ASYNC-FIX-20 by reusing an aiohttp ClientSession and setting concurrency to 20, noting that increasing the timeout was ineffective.  Minh p`
