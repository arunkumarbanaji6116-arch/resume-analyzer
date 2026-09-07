import re

QUESTIONS = {
    "Software Engineer": [
        {"category": "Technical Architecture", "text": "Tell me about a complex feature or system you designed and built end to end. What tradeoffs did you make?"},
        {"category": "Problem Solving", "text": "Describe a time when you had to debug an elusive, high-priority production bug. How did you isolate root cause?"},
        {"category": "Collaboration & Conflict", "text": "Tell me about a situation where you had a major technical disagreement with a teammate or lead. How did you resolve it?"},
        {"category": "System Scaling", "text": "How do you approach optimizing database queries and backend latency when traffic surges?"},
        {"category": "Ownership & Impact", "text": "Describe a project that did not go as planned or missed a deadline. What did you learn and how did you adjust?"}
    ],
    "Frontend Developer": [
        {"category": "Architecture & State", "text": "How do you decide between local component state, global state management, and server state caching in a large React/Next.js app?"},
        {"category": "Web Performance", "text": "Walk me through how you optimize Core Web Vitals (LCP, FID/INP, CLS) on a heavy web application."},
        {"category": "Component Design", "text": "Tell me about an accessible, reusable design system component you built from scratch. How did you ensure testability?"},
        {"category": "Cross-Functional", "text": "Describe a time a designer gave you an impractical or ambiguous UI specification. How did you collaborate to reach a solution?"},
        {"category": "Behavioral", "text": "Tell me about a time you had to deliver a critical frontend release under tight deadline pressure."}
    ],
    "Backend Developer": [
        {"category": "API & Data Modeling", "text": "Walk me through your thought process when designing a high-throughput REST or GraphQL API from scratch."},
        {"category": "Concurrency & Resilience", "text": "How do you prevent race conditions, implement distributed locks, and handle eventual consistency?"},
        {"category": "Database Tuning", "text": "Describe a time you diagnosed and resolved a severe database bottleneck or locking issue in production."},
        {"category": "System Tradeoffs", "text": "When would you choose an asynchronous message queue (e.g. Kafka, RabbitMQ) over synchronous HTTP communication?"},
        {"category": "Failure Recovery", "text": "Tell me about a production outage you responded to. What was the blast radius and what postmortem actions did you take?"}
    ],
    "Data Analyst": [
        {"category": "Business Impact", "text": "Walk me through an analytical finding you uncovered that directly changed a business or product decision."},
        {"category": "Data Quality", "text": "How do you validate messy or incomplete data before presenting insights to executive leadership?"},
        {"category": "Data Storytelling", "text": "Explain a complex statistical or predictive modeling result to an entirely non-technical stakeholder."},
        {"category": "Prioritization", "text": "Describe a time multiple teams requested urgent dashboard reports simultaneously. How did you prioritize?"},
        {"category": "Behavioral", "text": "Tell me about a time your data analysis contradicted the prevailing opinion of senior management. What did you do?"}
    ],
    "Product Manager": [
        {"category": "Product Strategy", "text": "How do you prioritize your product roadmap when balancing customer feature requests, tech debt, and strategic bets?"},
        {"category": "Metric Diagnostics", "text": "If a core engagement metric dropped by 18% week-over-week, walk me through your step-by-step diagnostic plan."},
        {"category": "Stakeholder Influence", "text": "Tell me about a time you had to say 'no' to an influential stakeholder or executive. How did you communicate the decision?"},
        {"category": "Launch & Iteration", "text": "Describe a product or feature launch that underperformed initial goals. How did you iterate post-launch?"},
        {"category": "Customer Discovery", "text": "How do you conduct customer discovery interviews to validate an unproven problem before committing engineering resources?"}
    ],
    "DevOps / Cloud Engineer": [
        {"category": "CI/CD & Automation", "text": "How do you design a zero-downtime deployment pipeline with automated canary testing and rollback mechanisms?"},
        {"category": "Incident Management", "text": "Describe how you diagnosed and resolved a major cloud infrastructure outage or network partition."},
        {"category": "Infrastructure as Code", "text": "How do you manage state and avoid drift in a multi-environment Terraform or Kubernetes setup?"},
        {"category": "Security & Compliance", "text": "Walk me through how you secure container images, manage secrets, and enforce least-privilege IAM policies."},
        {"category": "Cost Optimization", "text": "Tell me about an initiative where you analyzed and significantly reduced cloud infrastructure spend without degrading SLA."}
    ],
    "General": [
        {"category": "Career Motivation", "text": "Walk me through your background and the pivotal career decisions that led you to this role."},
        {"category": "Problem Solving", "text": "Describe the most challenging obstacle you overcame in the last 12 months. What was the outcome?"},
        {"category": "Leadership & Ownership", "text": "Tell me about a time you noticed an organizational or technical problem that was not your responsibility, but you stepped up to solve it."},
        {"category": "Adaptability", "text": "Describe a situation where project priorities completely changed halfway through. How did you adapt?"},
        {"category": "Constructive Feedback", "text": "Tell me about the toughest piece of critical feedback you received and how you actively worked to address it."}
    ]
}


def questions_for(role: str) -> list:
    return QUESTIONS.get(role, QUESTIONS["General"])


MCQ_QUESTIONS = {
    "Software Engineer": [
        {
            "category": "Data Structures & Algorithms",
            "text": "You need to implement an LRU (Least Recently Used) Cache with O(1) time complexity for both get(key) and put(key, value). Which combination of data structures is optimal?",
            "options": [
                {"id": "A", "text": "Array and Binary Search Tree"},
                {"id": "B", "text": "Hash Map and Doubly Linked List"},
                {"id": "C", "text": "Singly Linked List and Min-Heap"},
                {"id": "D", "text": "Trie and Queue"}
            ],
            "correct": "B",
            "explanation": "A Hash Map provides O(1) lookup to locate nodes, while a Doubly Linked List allows O(1) node removal and insertion at the head/tail to track recency."
        },
        {
            "category": "Concurrency & Threading",
            "text": "Which technique is most effective for preventing deadlocks across multiple threads requiring multiple shared mutex locks?",
            "options": [
                {"id": "A", "text": "Impose a strict, global total ordering on lock acquisition order"},
                {"id": "B", "text": "Increase thread priority for whichever thread started first"},
                {"id": "C", "text": "Double the lock timeout on every collision"},
                {"id": "D", "text": "Replace all mutex locks with infinite busy-wait spinlocks"}
            ],
            "correct": "A",
            "explanation": "Deadlocks require circular wait. Enforcing a global strict lock acquisition hierarchy guarantees that circular dependency cannot form."
        },
        {
            "category": "System Architecture",
            "text": "When horizontally scaling a stateful web application across multiple server instances behind a load balancer, what is the best practice for session management?",
            "options": [
                {"id": "A", "text": "Store sessions in local server memory and rely purely on sticky sessions"},
                {"id": "B", "text": "Offload session state to a shared distributed cache like Redis or Memcached"},
                {"id": "C", "text": "Store the entire session database in browser LocalStorage without encryption"},
                {"id": "D", "text": "Disable HTTP keep-alive to force new connections on every request"}
            ],
            "correct": "B",
            "explanation": "Decoupling session state to a centralized, high-speed distributed cache (e.g. Redis) allows any server instance to process any request statelessly."
        },
        {
            "category": "Database Internals",
            "text": "Why do relational database engines (like PostgreSQL and MySQL) prefer B-Tree / B+Tree indexes over Hash indexes for general primary keys?",
            "options": [
                {"id": "A", "text": "Hash indexes use more disk space than B-Trees"},
                {"id": "B", "text": "B-Trees efficiently support range queries, inequality comparisons (<, >), and ordered sorting"},
                {"id": "C", "text": "Hash indexes cannot handle string data types"},
                {"id": "D", "text": "B-Trees guarantee O(1) lookup time in all worst-case scenarios"}
            ],
            "correct": "B",
            "explanation": "Hash indexes only support exact equality checks (=). B-Trees maintain sorted order, making range scans (BETWEEN, >, <, ORDER BY) extremely efficient."
        },
        {
            "category": "API Protocol & Design",
            "text": "According to the HTTP/1.1 specification (RFC 7231), which of the following HTTP methods is defined as idempotent?",
            "options": [
                {"id": "A", "text": "POST"},
                {"id": "B", "text": "PUT"},
                {"id": "C", "text": "CONNECT"},
                {"id": "D", "text": "PATCH"}
            ],
            "correct": "B",
            "explanation": "An idempotent method can be called multiple times with the exact same side-effects on the server as a single call. PUT and DELETE are idempotent; POST is not."
        },
        {
            "category": "Software Design Principles",
            "text": "The Dependency Inversion Principle (the 'D' in SOLID) states that:",
            "options": [
                {"id": "A", "text": "High-level modules should depend on low-level database drivers directly"},
                {"id": "B", "text": "Classes should have multiple responsibilities to reduce the number of files"},
                {"id": "C", "text": "High-level modules should depend on abstractions/interfaces, not concrete implementations"},
                {"id": "D", "text": "Derived classes must completely replace their parent classes without extending them"}
            ],
            "correct": "C",
            "explanation": "Dependency Inversion decouples software components so high-level business logic is decoupled from volatile low-level details through clean interface abstractions."
        }
    ],
    "Frontend Developer": [
        {
            "category": "React Optimization",
            "text": "In modern React, what is the key distinction between the `useMemo` and `useCallback` hooks?",
            "options": [
                {"id": "A", "text": "`useMemo` caches a computed return value; `useCallback` caches a function instance definition"},
                {"id": "B", "text": "`useMemo` runs after DOM paint, while `useCallback` runs before mount"},
                {"id": "C", "text": "`useCallback` is asynchronous, while `useMemo` is strictly synchronous"},
                {"id": "D", "text": "There is no difference; `useCallback` is just an alias for `useMemo`"}
            ],
            "correct": "A",
            "explanation": "`useMemo(() => fn(), deps)` memoizes the result of calling a function. `useCallback(fn, deps)` memoizes the callback function reference itself."
        },
        {
            "category": "Web Performance & Core Web Vitals",
            "text": "What is the most frequent root cause of a poor Cumulative Layout Shift (CLS) score on web pages?",
            "options": [
                {"id": "A", "text": "Excessive CSS minification"},
                {"id": "B", "text": "Images, iframes, or dynamic ad slots rendered without explicit width and height aspect-ratio attributes"},
                {"id": "C", "text": "Using HTTP/2 multiplexing instead of HTTP/1.1"},
                {"id": "D", "text": "Loading JavaScript files via defer instead of async"}
            ],
            "correct": "B",
            "explanation": "When media elements lack explicit dimensions, the browser cannot reserve vertical space before layout, causing content below to abruptly jump when loaded."
        },
        {
            "category": "CSS & Browser Rendering",
            "text": "Which CSS properties can modern browser engines animate using the GPU Compositor thread without triggering layout reflow or repaint?",
            "options": [
                {"id": "A", "text": "width and height"},
                {"id": "B", "text": "transform and opacity"},
                {"id": "C", "text": "top, left, and margin"},
                {"id": "D", "text": "padding and font-size"}
            ],
            "correct": "B",
            "explanation": "Changes to `transform` and `opacity` bypass layout recalculation and raster repaint entirely, running smoothly at 60/120fps on the GPU compositor."
        },
        {
            "category": "Browser Security",
            "text": "What is the primary role of the Cross-Origin Resource Sharing (CORS) mechanism implemented by browsers?",
            "options": [
                {"id": "A", "text": "To prevent SQL injection on backend databases"},
                {"id": "B", "text": "To allow servers to specify which third-party web origins are permitted to read their sensitive responses"},
                {"id": "C", "text": "To encrypt passwords transmitted over plain HTTP"},
                {"id": "D", "text": "To automatically compress API responses using Brotli"}
            ],
            "correct": "B",
            "explanation": "Under the Same-Origin Policy, browsers block cross-origin AJAX by default. CORS HTTP headers (`Access-Control-Allow-Origin`) let servers selectively permit trusted origins."
        },
        {
            "category": "JavaScript Event Loop",
            "text": "Consider code scheduling both `Promise.resolve().then(...)` and `setTimeout(..., 0)`. How does the JavaScript Event Loop order their execution?",
            "options": [
                {"id": "A", "text": "The `setTimeout` callback always executes first as a macrotask"},
                {"id": "B", "text": "The `Promise.then` microtask executes first before the next macrotask turn"},
                {"id": "C", "text": "Execution order is completely randomized across browser engines"},
                {"id": "D", "text": "Both callbacks execute simultaneously on background parallel worker threads"}
            ],
            "correct": "B",
            "explanation": "The microtask queue (Promise callbacks, MutationObserver) is fully drained after the current synchronous script and before the next macrotask (timer, I/O) begins."
        },
        {
            "category": "Next.js & SSR",
            "text": "What is the fundamental difference between Static Site Generation (SSG) and Server-Side Rendering (SSR)?",
            "options": [
                {"id": "A", "text": "SSG renders HTML at build time, whereas SSR executes data fetching and renders HTML per incoming user request"},
                {"id": "B", "text": "SSG is only for mobile apps; SSR is only for desktop browsers"},
                {"id": "C", "text": "SSR requires zero servers; SSG requires a cluster of Node.js servers"},
                {"id": "D", "text": "SSG does not support JavaScript or interactive React components"}
            ],
            "correct": "A",
            "explanation": "SSG compiles static HTML pages ahead-of-time during CI/CD build to be cached on CDNs. SSR dynamically fetches data and renders HTML in real time for every request."
        }
    ],
    "Backend Developer": [
        {
            "category": "Database Transactions",
            "text": "In relational database ACID properties, which transaction isolation level prevents 'Phantom Reads' (where new rows inserted by another transaction become visible)?",
            "options": [
                {"id": "A", "text": "Read Uncommitted"},
                {"id": "B", "text": "Read Committed"},
                {"id": "C", "text": "Repeatable Read (in ANSI SQL) / Serializable"},
                {"id": "D", "text": "Snapshot Isolation without MVCC"}
            ],
            "correct": "C",
            "explanation": "Serializable (and Repeatable Read in MVCC engines like Postgres) enforces range locks or predicate locks that prevent phantom rows from appearing during queries."
        },
        {
            "category": "Distributed Caching",
            "text": "What is a 'Cache Stampede' (Thundering Herd) and how is it most reliably resolved in high-throughput backend services?",
            "options": [
                {"id": "A", "text": "When cache memory runs out; resolved by rebooting the Redis cluster"},
                {"id": "B", "text": "When a hot cache key expires and thousands of concurrent requests simultaneously hit the database; resolved via distributed mutex locks or probabilistic early recomputation"},
                {"id": "C", "text": "When cache keys contain invalid UTF-8 characters; resolved by URL encoding keys"},
                {"id": "D", "text": "When a cache node disconnects from the load balancer; resolved by increasing TCP timeouts"}
            ],
            "correct": "B",
            "explanation": "A cache stampede occurs when a high-traffic key expires, overwhelming the DB. Using a distributed lock ensures only one worker rebuilds the cache while others wait or receive stale data."
        },
        {
            "category": "Message Streaming & Queues",
            "text": "When designing an asynchronous messaging system with Apache Kafka or RabbitMQ, what design requirement does 'At-Least-Once' delivery impose on consumers?",
            "options": [
                {"id": "A", "text": "Consumer services must be completely stateless and run on a single thread"},
                {"id": "B", "text": "Consumer message handlers must be idempotent to safely handle duplicate message deliveries"},
                {"id": "C", "text": "All messages must be processed strictly within 10 milliseconds"},
                {"id": "D", "text": "Messages must be deleted from the broker before consumers process them"}
            ],
            "correct": "B",
            "explanation": "At-least-once delivery guarantees no message is lost, but retries and network blips can produce duplicate deliveries. Consumers must be idempotent (e.g. deduplication keys)."
        },
        {
            "category": "Authentication & Security",
            "text": "Which algorithm and approach should modern backend services use to store user authentication passwords safely?",
            "options": [
                {"id": "A", "text": "Fast cryptographic hashing like SHA-256 with an MD5 salt"},
                {"id": "B", "text": "A compute-heavy, memory-hard adaptive key derivation function like bcrypt or Argon2id with unique salt and high work factor"},
                {"id": "C", "text": "Two-way AES-256 encryption with a hardcoded static server key"},
                {"id": "D", "text": "Base64 encoding with rot13 masking"}
            ],
            "correct": "B",
            "explanation": "Passwords must use slow, adaptive algorithms (bcrypt, Argon2id, PBKDF2) designed to resist GPU-based brute force and rainbow table dictionary attacks."
        },
        {
            "category": "Distributed Systems & CAP",
            "text": "According to the CAP Theorem, when an unavoidable network partition (P) occurs between distributed database nodes, what architectural trade-off must be made?",
            "options": [
                {"id": "A", "text": "The system must automatically switch from SQL to NoSQL"},
                {"id": "B", "text": "Choose between Consistency (rejecting stale writes/reads) or Availability (accepting reads/writes that may be temporarily inconsistent)"},
                {"id": "C", "text": "Sacrifice durability to maintain both 100% availability and strict consistency"},
                {"id": "D", "text": "All transactions must be aborted and the cluster shutdown"}
            ],
            "correct": "B",
            "explanation": "Network partitions in distributed systems are inevitable. When a split occurs, an architecture must either prioritize Consistency (CP) or Availability (AP)."
        },
        {
            "category": "Database Performance",
            "text": "What is the primary danger of the 'N+1 Query Problem' in ORM frameworks (like Hibernate, Prisma, or SQLAlchemy)?",
            "options": [
                {"id": "A", "text": "It causes compile-time type mismatch errors"},
                {"id": "B", "text": "Instead of executing a single JOIN query, the ORM issues one query for parent records plus N separate queries for each child record, severely degrading latency"},
                {"id": "C", "text": "It prevents database connections from closing cleanly"},
                {"id": "D", "text": "It consumes all disk storage on the database host"}
            ],
            "correct": "B",
            "explanation": "The N+1 problem occurs when querying parent entities lazily triggers a separate round-trip query for every child relationship, easily multiplying database round-trips into hundreds."
        }
    ],
    "Data Analyst": [
        {
            "category": "SQL & Aggregations",
            "text": "In SQL, what is the key functional difference between the `WHERE` clause and the `HAVING` clause?",
            "options": [
                {"id": "A", "text": "`WHERE` filters individual rows before grouping; `HAVING` filters aggregated group results after `GROUP BY`"},
                {"id": "B", "text": "`HAVING` can only be used with `SELECT *`, while `WHERE` requires specific column names"},
                {"id": "C", "text": "`WHERE` is only available in MySQL; `HAVING` is PostgreSQL specific"},
                {"id": "D", "text": "`WHERE` executes after aggregations like `SUM()` and `AVG()`"}
            ],
            "correct": "A",
            "explanation": "`WHERE` operates on individual rows prior to any group aggregation. `HAVING` filters the results of aggregate functions (`COUNT(*) > 5`) after grouping."
        },
        {
            "category": "Statistics & Analytics",
            "text": "When analyzing a continuous revenue dataset with extreme positive skewness (e.g. a few multi-million dollar enterprise accounts among millions of free users), which measure of central tendency is most reliable?",
            "options": [
                {"id": "A", "text": "Arithmetic Mean"},
                {"id": "B", "text": "Median (and Interquartile Range)"},
                {"id": "C", "text": "Mode only"},
                {"id": "D", "text": "Standard Deviation alone"}
            ],
            "correct": "B",
            "explanation": "The mean is heavily distorted by extreme outlier values. The median provides the true 50th percentile midpoint and resists outlier skew."
        },
        {
            "category": "SQL Window Functions",
            "text": "How do the SQL window functions `RANK()` and `DENSE_RANK()` behave when encountering duplicate tied values in an `ORDER BY` partition?",
            "options": [
                {"id": "A", "text": "Neither handles duplicates; both throw runtime syntax errors"},
                {"id": "B", "text": "`RANK()` skips subsequent rank numbers after ties (e.g. 1, 2, 2, 4); `DENSE_RANK()` assigns consecutive ranks without gaps (e.g. 1, 2, 2, 3)"},
                {"id": "C", "text": "`DENSE_RANK()` skips ranks; `RANK()` does not"},
                {"id": "D", "text": "`RANK()` is nondeterministic, while `DENSE_RANK()` randomly assigns order"}
            ],
            "correct": "B",
            "explanation": "`RANK()` leaves gaps in rank numbers equal to the tie count. `DENSE_RANK()` keeps consecutive integer rankings regardless of how many ties exist."
        },
        {
            "category": "A/B Testing & Experimentation",
            "text": "In an A/B testing experiment, what does a statistically significant p-value of less than 0.05 (p < 0.05) formally indicate?",
            "options": [
                {"id": "A", "text": "There is a 95% certainty that the new variant will increase revenue by at least 5%"},
                {"id": "B", "text": "Under the null hypothesis that there is no true difference, the probability of observing this result by random variance alone is under 5%"},
                {"id": "C", "text": "The experiment ran for less than 5 days"},
                {"id": "D", "text": "Exactly 5% of users dropped off during checkout"}
            ],
            "correct": "B",
            "explanation": "A p-value measures the probability of obtaining test results at least as extreme as observed, assuming the null hypothesis (no real effect) is true."
        },
        {
            "category": "Cohort Analysis",
            "text": "What is the primary analytical objective of a Cohort Retention Heatmap in product analytics?",
            "options": [
                {"id": "A", "text": "To monitor server CPU load across geographical timezones"},
                {"id": "B", "text": "To track whether user groups acquired in specific time periods remain active and engaged over subsequent days, weeks, or months"},
                {"id": "C", "text": "To count total page views across marketing channels without considering dates"},
                {"id": "D", "text": "To measure the cost per click for paid search campaigns"}
            ],
            "correct": "B",
            "explanation": "Cohort analysis groups users by a shared acquisition event (e.g. sign-up week) to evaluate how retention curves evolve over product iterations."
        },
        {
            "category": "Data Modeling",
            "text": "In a Star Schema data warehouse architecture, what characterizes Fact tables compared to Dimension tables?",
            "options": [
                {"id": "A", "text": "Fact tables contain descriptive text; Dimension tables contain foreign keys"},
                {"id": "B", "text": "Fact tables contain quantitative metrics, event timestamps, and foreign keys; Dimension tables contain descriptive business attributes (who, what, where)"},
                {"id": "C", "text": "Fact tables are always smaller than Dimension tables"},
                {"id": "D", "text": "Fact tables cannot contain numeric measurements"}
            ],
            "correct": "B",
            "explanation": "Fact tables record transactional events and numeric measurements (e.g., sales quantity, revenue), surrounded by Dimension tables that provide context (customer, product, store)."
        }
    ],
    "Product Manager": [
        {
            "category": "Prioritization Frameworks",
            "text": "In the popular RICE prioritization framework, how is the composite priority score mathematically calculated?",
            "options": [
                {"id": "A", "text": "(Reach + Impact + Confidence) - Effort"},
                {"id": "B", "text": "(Reach × Impact × Confidence) / Effort"},
                {"id": "C", "text": "(Effort × Impact) / (Reach × Confidence)"},
                {"id": "D", "text": "Reach × Impact × Confidence × Effort"}
            ],
            "correct": "B",
            "explanation": "RICE balances value creation against engineering costs: Reach (users affected) × Impact (effect per user) × Confidence (evidence factor) divided by Effort (person-months)."
        },
        {
            "category": "Experimentation & Metrics",
            "text": "When running an experiment aimed at increasing checkout conversion, why must a Product Manager establish 'Guardrail Metrics' (Counter-Metrics)?",
            "options": [
                {"id": "A", "text": "To guarantee that the engineering team works overtime"},
                {"id": "B", "text": "To detect unintentional negative side effects, such as a spike in refund requests, cart abandonment, or customer support tickets"},
                {"id": "C", "text": "To ensure that every experiment concludes with positive revenue"},
                {"id": "D", "text": "To bypass executive review if the primary metric improves"}
            ],
            "correct": "B",
            "explanation": "A guardrail metric safeguards against unintended damage. For instance, an aggressive discount might boost conversion but severely reduce profit margins or increase fraud."
        },
        {
            "category": "Product Strategy",
            "text": "What is the core distinction between a 'Leading Indicator' metric and a 'Lagging Indicator' metric?",
            "options": [
                {"id": "A", "text": "Leading indicators measure future outcomes based on present user behaviors; lagging indicators confirm historical results that have already occurred"},
                {"id": "B", "text": "Leading indicators are financial; lagging indicators are operational"},
                {"id": "C", "text": "Lagging indicators predict customer churn before it happens"},
                {"id": "D", "text": "Leading indicators can only be measured once per fiscal year"}
            ],
            "correct": "A",
            "explanation": "Leading indicators (e.g., weekly active users completing a core onboarding action) predict future trajectory. Lagging indicators (e.g., quarterly churn or net revenue) reflect past performance."
        },
        {
            "category": "Product Discovery",
            "text": "According to continuous product discovery best practices (Teresa Torres, Marty Cagan), what is the most effective approach to user interview questions?",
            "options": [
                {"id": "A", "text": "Ask users to predict if they would purchase a hypothetical feature in 6 months"},
                {"id": "B", "text": "Ask users to walk through specific, recent stories of how they actually experienced the problem in real life"},
                {"id": "C", "text": "Pitch the solution immediately and ask for a rating from 1 to 10"},
                {"id": "D", "text": "Show complete high-fidelity mockups and ask if they like the color palette"}
            ],
            "correct": "B",
            "explanation": "Users are notoriously poor at predicting hypothetical future behaviors. Asking about specific past stories uncovers genuine habits, workarounds, and painful friction points."
        },
        {
            "category": "Go-To-Market & Growth",
            "text": "What is the hallmark characteristic of a Product-Led Growth (PLG) business model compared to traditional sales-led models?",
            "options": [
                {"id": "A", "text": "The company relies solely on expensive outbound cold callers"},
                {"id": "B", "text": "The product experience itself (freemium, self-serve onboarding, viral loops) serves as the primary driver of acquisition, retention, and expansion"},
                {"id": "C", "text": "The product is only sold via multi-year enterprise RFP contracts"},
                {"id": "D", "text": "Engineering does not release software updates without marketing approval"}
            ],
            "correct": "B",
            "explanation": "In PLG (like Slack, Figma, Dropbox), end-users discover, adopt, and experience rapid 'Time-to-Value' self-serviced, organically spreading the tool inside organizations."
        },
        {
            "category": "Stakeholder Management",
            "text": "A key enterprise client demands a bespoke, one-off feature that will derail your team's roadmap for two quarters. How should an executive PM navigate this?",
            "options": [
                {"id": "A", "text": "Agree immediately to avoid losing the account and force engineers into crunch time"},
                {"id": "B", "text": "Deeply investigate the underlying problem the client wants to solve to see if an extensible, roadmap-aligned solution can address it without bespoke code"},
                {"id": "C", "text": "Ignore the email and hope the client forgets about the request"},
                {"id": "D", "text": "Blame the engineering lead and tell the client that tech debt makes it impossible"}
            ],
            "correct": "B",
            "explanation": "Great PMs separate the client's requested solution from their actual underlying objective. Uncovering the true pain point often reveals an elegant general solution that benefits all users."
        }
    ],
    "DevOps / Cloud Engineer": [
        {
            "category": "Kubernetes Architecture",
            "text": "In a standard Kubernetes control plane, which core component is responsible for assigning unassigned Pods to available worker nodes based on resource constraints?",
            "options": [
                {"id": "A", "text": "kube-apiserver"},
                {"id": "B", "text": "kube-scheduler"},
                {"id": "C", "text": "etcd"},
                {"id": "D", "text": "kubelet"}
            ],
            "correct": "B",
            "explanation": "`kube-scheduler` watches for newly created pods without an assigned node and selects the optimal node for them based on affinity, taints, and resource requirements."
        },
        {
            "category": "Deployment Strategies",
            "text": "How does a Canary Deployment strategy differ fundamentally from a Blue-Green Deployment strategy?",
            "options": [
                {"id": "A", "text": "Canary deployments require shutting down the database during upgrades"},
                {"id": "B", "text": "Canary routes a small percentage (e.g. 5%) of live traffic to the new version to monitor error rates before rolling out; Blue-Green switches 100% of traffic at once"},
                {"id": "C", "text": "Blue-Green deployments do not require duplicate environments"},
                {"id": "D", "text": "Canary deployment can only be used with bare-metal servers"}
            ],
            "correct": "B",
            "explanation": "Canary releases introduce changes to a tiny cohort of live users to validate telemetry and error rates. Blue-green maintains two identical full production clusters and swaps router traffic."
        },
        {
            "category": "Infrastructure as Code",
            "text": "In HashiCorp Terraform, what is the primary purpose of configuring Remote State with state locking (e.g. AWS S3 + DynamoDB)?",
            "options": [
                {"id": "A", "text": "To auto-generate Docker container images"},
                {"id": "B", "text": "To prevent concurrent CI/CD pipelines from applying conflicting changes simultaneously and corrupting cloud resource metadata"},
                {"id": "C", "text": "To eliminate the need for writing HCL configuration files"},
                {"id": "D", "text": "To bypass cloud provider billing meters"}
            ],
            "correct": "B",
            "explanation": "State locking ensures that only one pipeline or engineer can execute `terraform apply` at a time, preventing state file collisions and resource corruption."
        },
        {
            "category": "Docker & Container Security",
            "text": "What is the best practice for hardening production Docker container images and minimizing security attack surface?",
            "options": [
                {"id": "A", "text": "Install debugging tools like `curl`, `gdb`, and `telnet` in the production layer"},
                {"id": "B", "text": "Use multi-stage builds, non-root users, and minimal base images (e.g., distroless or Alpine) without unnecessary package managers"},
                {"id": "C", "text": "Always run the container process as `root` with `privileged: true`"},
                {"id": "D", "text": "Store database passwords in plaintext `ENV` declarations in the Dockerfile"}
            ],
            "correct": "B",
            "explanation": "Multi-stage builds leave compilers and build tooling behind. Non-root users and minimal distroless bases dramatically slash CVE vulnerabilities and prevent container breakout."
        },
        {
            "category": "Cloud Security & IAM",
            "text": "The Principle of Least Privilege (PoLP) in cloud infrastructure dictates that:",
            "options": [
                {"id": "A", "text": "All developers should share an AdministratorAccess AWS IAM role to speed up development"},
                {"id": "B", "text": "Identities and services must only be granted the bare minimum permissions necessary to perform their legitimate function"},
                {"id": "C", "text": "Firewalls should allow inbound traffic on all ports by default"},
                {"id": "D", "text": "Services should authenticate using long-lived API keys committed to Git"}
            ],
            "correct": "B",
            "explanation": "Least privilege strictly bounds access rights, ensuring that if any single service or credential is breached, the attacker's blast radius remains severely restricted."
        },
        {
            "category": "Observability & SRE",
            "text": "According to Google SRE and modern observability standards, what are the 'Three Pillars of Observability'?",
            "options": [
                {"id": "A", "text": "CPU, Memory, and Disk"},
                {"id": "B", "text": "Metrics, Logs, and Distributed Traces"},
                {"id": "C", "text": "Authentication, Authorization, and Accounting"},
                {"id": "D", "text": "Development, Staging, and Production"}
            ],
            "correct": "B",
            "explanation": "Metrics provide aggregated real-time health indicators; Logs provide detailed transactional event records; Distributed Traces pinpoint end-to-end request latency across microservices."
        }
    ],
    "General": [
        {
            "category": "Conflict & Stakeholder Management",
            "text": "When two senior stakeholders have conflicting requirements for a project deadline, what is the best professional response?",
            "options": [
                {"id": "A", "text": "Secretly follow whoever is higher on the organizational chart and ignore the other"},
                {"id": "B", "text": "Map out the trade-offs of both options against overarching business goals and host a collaborative alignment session"},
                {"id": "C", "text": "Stop all project work until they resolve their argument independently"},
                {"id": "D", "text": "Commit to 100% of both sets of requirements without asking for additional resources"}
            ],
            "correct": "B",
            "explanation": "Professional leadership involves anchoring trade-offs to shared corporate objectives and facilitating clear, data-informed alignment rather than taking sides or ignoring conflict."
        },
        {
            "category": "Root Cause Analysis",
            "text": "What is the primary objective of the '5 Whys' root cause analysis technique commonly used in engineering postmortems?",
            "options": [
                {"id": "A", "text": "To find which engineer to blame and reprimand for the incident"},
                {"id": "B", "text": "To drill down through consecutive layers of cause and effect until the underlying systemic flaw is identified"},
                {"id": "C", "text": "To create five alternative excuses for external clients"},
                {"id": "D", "text": "To make postmortem meetings take at least five hours"}
            ],
            "correct": "B",
            "explanation": "By repeatedly asking 'Why?', teams bypass superficial symptoms and uncover systemic, cultural, or process root causes to implement permanent safeguards."
        },
        {
            "category": "Communication & Proactive Ownership",
            "text": "You realize a critical project milestone will be delayed by two weeks. When and how should this be communicated to leadership?",
            "options": [
                {"id": "A", "text": "Wait until the original delivery day so they don't worry in advance"},
                {"id": "B", "text": "Proactively communicate as soon as the risk is confirmed, outlining the root causes, revised timeline, and mitigation options"},
                {"id": "C", "text": "Send a vague message on Friday night after everyone has left the office"},
                {"id": "D", "text": "Ship an untested, broken release on time and fix bugs later in secret"}
            ],
            "correct": "B",
            "explanation": "Early, proactive communication demonstrates executive maturity, builds stakeholder trust, and gives the business time to adjust dependencies or reallocate support."
        },
        {
            "category": "Agile & Continuous Improvement",
            "text": "In Scrum methodology, what is the dedicated purpose of the Sprint Retrospective meeting?",
            "options": [
                {"id": "A", "text": "To demo completed software features to external end-users and investors"},
                {"id": "B", "text": "For the team to inspect their own workflow, processes, and teamwork, and agree on actionable improvements for the next sprint"},
                {"id": "C", "text": "To perform quarterly individual employee compensation evaluations"},
                {"id": "D", "text": "To assign daily Jira story points for the upcoming 6 months"}
            ],
            "correct": "B",
            "explanation": "The Sprint Retrospective is an internal reflection meeting for the Scrum team to examine what went well, what had friction, and enact concrete process upgrades."
        },
        {
            "category": "Leadership & Feedback",
            "text": "When providing constructive feedback to a peer on substandard work, which framework delivers the most positive behavioral outcome?",
            "options": [
                {"id": "A", "text": "Describe the specific observed situation and behavior, explain the impact on the team, and suggest actionable improvements (SBI model)"},
                {"id": "B", "text": "Make broad generalizations like 'You always make mistakes' in a public Slack channel"},
                {"id": "C", "text": "Avoid giving any feedback and fix their mistakes yourself every time"},
                {"id": "D", "text": "Complain to HR without speaking to the teammate first"}
            ],
            "correct": "A",
            "explanation": "The Situation-Behavior-Impact (SBI) framework focuses objectively on observable facts and tangible impact, avoiding personal attacks and fostering psychological safety."
        },
        {
            "category": "Time & Priority Management",
            "text": "In the Eisenhower Decision Matrix, which quadrant should high-performing professionals prioritize to prevent constant firefighting?",
            "options": [
                {"id": "A", "text": "Quadrant 1: Urgent and Important (Immediate crises)"},
                {"id": "B", "text": "Quadrant 2: Not Urgent but Highly Important (Strategic planning, refactoring, learning, relationships)"},
                {"id": "C", "text": "Quadrant 3: Urgent but Not Important (Constant interruptions and trivial requests)"},
                {"id": "D", "text": "Quadrant 4: Not Urgent and Not Important (Time-wasting busywork)"}
            ],
            "correct": "B",
            "explanation": "Investing time in Quadrant 2 (Not Urgent, but Important) prevents problems before they become emergency crises (Quadrant 1), driving sustained high performance."
        }
    ]
}


def mcq_questions_for(role: str) -> list:
    return MCQ_QUESTIONS.get(role, MCQ_QUESTIONS["General"])


STAR_KEYWORDS = {
    "situation": ["situation", "context", "background", "when", "company", "project", "client", "team", "working at", "faced"],
    "task": ["task", "goal", "target", "needed to", "responsible for", "objective", "challenge", "assigned", "requirement"],
    "action": ["built", "designed", "developed", "led", "created", "implemented", "refactored", "analyzed", "coordinated", "resolved", "spearheaded", "executed"],
    "result": ["result", "impact", "increased", "decreased", "reduced", "improved", "saved", "%", "percent", "metric", "revenue", "achieved", "learned", "outcome"]
}


def assess_answer(answer: str, question: str = "") -> dict:
    text = answer.strip()
    words = re.findall(r"\b[\w+#.-]+\b", text.lower())
    word_count = len(words)

    if word_count < 10:
        return {
            "score": 25,
            "star": {"situation": False, "task": False, "action": False, "result": False},
            "strengths": ["Answer was submitted."],
            "improvements": ["Your answer is too brief. Provide a structured response with context, actions, and quantifiable results."],
            "feedback": "Answer is too short. Use the STAR technique to explain the Situation, your Task, concrete Actions, and measurable Results."
        }

    try:
        from ai.gemini_client import gemini_assess_interview
        gemini_result = gemini_assess_interview(answer, question)
        if gemini_result:
            return gemini_result
    except Exception:
        pass

    text_lower = text.lower()
    has_situation = any(k in text_lower for k in STAR_KEYWORDS["situation"]) or word_count > 60
    has_task = any(k in text_lower for k in STAR_KEYWORDS["task"])
    has_action = any(k in text_lower for k in STAR_KEYWORDS["action"])
    has_result = any(k in text_lower for k in STAR_KEYWORDS["result"]) or bool(re.search(r"\b\d+[%+]?\b", text))

    star_count = sum([has_situation, has_task, has_action, has_result])

    # Base scoring algorithm
    score = 40
    # Length points (target: 80 - 220 words)
    if word_count >= 80:
        score += 20
    elif word_count >= 40:
        score += 10

    # STAR structure points
    score += star_count * 9

    # Quantified metrics bonus
    metrics = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text))
    if metrics >= 2:
        score += 8
    elif metrics == 1:
        score += 4

    score = min(98, max(30, score))

    strengths = []
    improvements = []

    if has_action:
        strengths.append("Strong active verbs demonstrating personal ownership.")
    if has_result or metrics > 0:
        strengths.append("Included tangible business or technical results.")
    if word_count >= 75:
        strengths.append("Sufficient narrative depth and detail.")
    if not strengths:
        strengths.append("Good start addressing the prompt directly.")

    if not has_result:
        improvements.append("Quantify the final result (e.g. % performance boost, time saved, revenue generated).")
    if not has_task:
        improvements.append("Clarify your specific responsibility or task within the larger team.")
    if word_count < 65:
        improvements.append("Expand on the technical or procedural decisions you made during the project.")
    if word_count > 300:
        improvements.append("Keep your answer concise (aim for ~90-180 words) to avoid rambling.")

    if score >= 80:
        feedback = "Outstanding response. Clear STAR structure, concrete actions, and impactful outcome."
    elif score >= 65:
        feedback = "Solid answer. Strengthen with more specific metrics or sharper action verbs."
    else:
        feedback = "Needs more structure. Detail your exact actions and the final measurable outcome using the STAR format."

    return {
        "score": score,
        "word_count": word_count,
        "star": {
            "situation": has_situation,
            "task": has_task,
            "action": has_action,
            "result": has_result
        },
        "strengths": strengths,
        "improvements": improvements or ["Continue practicing for fluid, confident delivery."],
        "feedback": feedback
    }
