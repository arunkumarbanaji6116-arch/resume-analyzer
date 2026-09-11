# Expanded interview question bank & evaluation engine
import random
import re

QUESTIONS = {
    "Software Engineer": [
        {"category": "Technical Architecture", "text": "Tell me about a complex feature or system you designed and built end to end. What tradeoffs did you make?"},
        {"category": "Problem Solving", "text": "Describe a time when you had to debug an elusive, high-priority production bug. How did you isolate root cause?"},
        {"category": "Collaboration & Conflict", "text": "Tell me about a situation where you had a major technical disagreement with a teammate or lead. How did you resolve it?"},
        {"category": "System Scaling", "text": "How do you approach optimizing database queries and backend latency when traffic surges?"},
        {"category": "Ownership & Impact", "text": "Describe a project that did not go as planned or missed a deadline. What did you learn and how did you adjust?"},
        {"category": "Distributed Systems", "text": "Walk me through how you implement distributed locking and ensure idempotency across multiple microservice boundaries."},
        {"category": "Legacy Migration", "text": "Describe a time you migrated a critical legacy monolith service to modern architecture without causing downtime for users."},
        {"category": "Code Quality & Mentorship", "text": "How do you conduct code reviews to balance velocity, maintainability, and constructive feedback for junior engineers?"},
        {"category": "Caching Architecture", "text": "Explain your approach to designing a multi-tier caching system. How do you prevent cache stampedes and stale reads?"},
        {"category": "Incident Response", "text": "Describe the highest-severity outage you responded to as an on-call engineer. How did you triage, mitigate, and conduct the blameless postmortem?"},
        {"category": "API Contract Design", "text": "How do you design, version, and evolve public APIs to ensure zero breaking changes for thousands of existing clients?"},
        {"category": "Security Engineering", "text": "Walk me through how you identify and mitigate security vulnerabilities (e.g. injection, auth bypass, SSRF) during system design."},
        {"category": "Technical Debt", "text": "Tell me about an initiative where you successfully convinced product managers to allocate engineering time to pay down critical technical debt."},
        {"category": "Performance Profiling", "text": "Describe a scenario where a service had severe memory leaks or high CPU utilization. What tools and profiling steps did you take?"},
        {"category": "Automated Testing", "text": "How do you architect an end-to-end testing strategy across unit, integration, and contract tests to maintain 99.9% release confidence?"}
    ],
    "Frontend Developer": [
        {"category": "Architecture & State", "text": "How do you decide between local component state, global state management, and server state caching in a large React/Next.js app?"},
        {"category": "Web Performance", "text": "Walk me through how you optimize Core Web Vitals (LCP, FID/INP, CLS) on a heavy web application."},
        {"category": "Component Design", "text": "Tell me about an accessible, reusable design system component you built from scratch. How did you ensure testability?"},
        {"category": "Cross-Functional", "text": "Describe a time a designer gave you an impractical or ambiguous UI specification. How did you collaborate to reach a solution?"},
        {"category": "Behavioral", "text": "Tell me about a time you had to deliver a critical frontend release under tight deadline pressure."},
        {"category": "Hydration & Rendering", "text": "Describe how you diagnose and fix hydration mismatches and rendering waterfalls in Server-Side Rendered (SSR) applications."},
        {"category": "Real-Time Web", "text": "How do you implement optimistic UI updates with WebSocket or SSE synchronization while handling connection drops gracefully?"},
        {"category": "Bundle Optimization", "text": "Walk me through how you analyzed and reduced JavaScript bundle sizes using code splitting, dynamic imports, and tree-shaking."},
        {"category": "Web Accessibility (a11y)", "text": "Tell me about an initiative where you audited and refactored a complex interactive widget to meet WCAG 2.1 AA accessibility standards."},
        {"category": "Memory Leaks", "text": "Describe a time you investigated and resolved a browser memory leak caused by dangling event listeners or retained closures in a single-page app."},
        {"category": "Micro-Frontends", "text": "What are the engineering trade-offs of micro-frontends and Module Federation compared to a well-structured modular monorepo?"},
        {"category": "Browser Security", "text": "How do you protect modern single-page applications against Cross-Site Scripting (XSS), CSRF, and supply-chain npm vulnerabilities?"},
        {"category": "Responsive Complex UI", "text": "Describe how you built a data-dense, interactive dashboard that maintained 60 FPS scrolling and rendering across both desktop and mobile."},
        {"category": "Modern CSS Architecture", "text": "How do you approach modern CSS architecture (Tailwind vs CSS Modules vs CSS-in-JS) regarding bundle size and runtime overhead?"},
        {"category": "Frontend Testing", "text": "How do you design a comprehensive UI testing pyramid balancing Jest/Vitest unit tests with Playwright/Cypress end-to-end user journeys?"}
    ],
    "Backend Developer": [
        {"category": "API & Data Modeling", "text": "Walk me through your thought process when designing a high-throughput REST or GraphQL API from scratch."},
        {"category": "Concurrency & Resilience", "text": "How do you prevent race conditions, implement distributed locks, and handle eventual consistency?"},
        {"category": "Database Tuning", "text": "Describe a time you diagnosed and resolved a severe database bottleneck or locking issue in production."},
        {"category": "System Tradeoffs", "text": "When would you choose an asynchronous message queue (e.g. Kafka, RabbitMQ) over synchronous HTTP communication?"},
        {"category": "Failure Recovery", "text": "Tell me about a production outage you responded to. What was the blast radius and what postmortem actions did you take?"},
        {"category": "Zero-Downtime Migration", "text": "How do you execute schema migrations on multi-terabyte production databases without locking tables or degrading read/write traffic?"},
        {"category": "Distributed Transactions", "text": "Explain how you implement the Saga pattern with compensating transactions across multiple distributed microservices."},
        {"category": "Rate Limiting & Throttling", "text": "Describe how you built or configured a distributed rate limiter to defend APIs against abusive traffic spikes."},
        {"category": "Connection Pool Exhaustion", "text": "Tell me about an incident where database or HTTP client connection pools were exhausted. How did you troubleshoot and reconfigure them?"},
        {"category": "Event-Driven Systems", "text": "How do you ensure message ordering, exactly-once processing semantics, and dead-letter queue retries in an event-driven architecture?"},
        {"category": "Authentication & Session", "text": "Walk me through the security trade-offs of stateless JWTs versus stateful server sessions in large-scale multi-service ecosystems."},
        {"category": "Background Processing", "text": "How do you architect a scalable background task queue capable of handling millions of delayed and recurring jobs reliably?"},
        {"category": "Database Partitioning", "text": "When and how do you introduce horizontal sharding versus vertical partitioning for an exponentially growing database?"},
        {"category": "Observability & Tracing", "text": "Describe how you implemented distributed tracing across microservices using OpenTelemetry to pinpoint latency bottlenecks."},
        {"category": "Resilience Patterns", "text": "How do you configure circuit breakers, exponential backoffs, and jitter to avoid cascading thundering-herd failures?"}
    ],
    "Data Analyst": [
        {"category": "Business Impact", "text": "Walk me through an analytical finding you uncovered that directly changed a business or product decision."},
        {"category": "Data Quality", "text": "How do you validate messy or incomplete data before presenting insights to executive leadership?"},
        {"category": "Data Storytelling", "text": "Explain a complex statistical or predictive modeling result to an entirely non-technical stakeholder."},
        {"category": "Prioritization", "text": "Describe a time multiple teams requested urgent dashboard reports simultaneously. How did you prioritize?"},
        {"category": "Behavioral", "text": "Tell me about a time your data analysis contradicted the prevailing opinion of senior management. What did you do?"},
        {"category": "A/B Testing & Rigor", "text": "Walk me through how you calculate sample size, minimum detectable effect, and guard against p-hacking in an experimentation program."},
        {"category": "Cohort Retention", "text": "Describe how you performed cohort and user-churn analysis to identify the exact moments users abandon a digital product."},
        {"category": "Metric Definition", "text": "Tell me about a situation where different departments had conflicting definitions of a core KPI (like Active User). How did you align them?"},
        {"category": "SQL Optimization", "text": "Describe an instance where an analytical query on Snowflake/BigQuery was too slow or expensive. How did you optimize it?"},
        {"category": "Anomaly Investigation", "text": "If a key revenue or acquisition metric dropped by 25% overnight, what is your systematic troubleshooting checklist?"},
        {"category": "Funnel Optimization", "text": "How do you analyze multi-step conversion funnels to isolate drop-off friction and propose testable conversion rate optimizations?"},
        {"category": "Executive Dashboarding", "text": "What principles do you follow when designing executive-level dashboards to prevent information overload while delivering actionable alerts?"},
        {"category": "ETL Collaboration", "text": "Describe a time you collaborated with data engineers when upstream data pipelines were broken or delivering delayed data."},
        {"category": "Predictive Modeling", "text": "Tell me about a predictive regression or classification model you built to forecast customer lifetime value or sales pipeline."},
        {"category": "Ethical Data Handling", "text": "How do you ensure user privacy, GDPR compliance, and eliminate bias when analyzing sensitive demographic or user behavior data?"}
    ],
    "Product Manager": [
        {"category": "Product Strategy", "text": "How do you prioritize your product roadmap when balancing customer feature requests, tech debt, and strategic bets?"},
        {"category": "Metric Diagnostics", "text": "If a core engagement metric dropped by 18% week-over-week, walk me through your step-by-step diagnostic plan."},
        {"category": "Stakeholder Influence", "text": "Tell me about a time you had to say 'no' to an influential stakeholder or executive. How did you communicate the decision?"},
        {"category": "Launch & Iteration", "text": "Describe a product or feature launch that underperformed initial goals. How did you iterate post-launch?"},
        {"category": "Customer Discovery", "text": "How do you conduct customer discovery interviews to validate an unproven problem before committing engineering resources?"},
        {"category": "MVP Scoping", "text": "Describe a time you had to dramatically ruthlessly cut scope from a planned release to meet an urgent market deadline."},
        {"category": "Feature Sunset", "text": "Walk me through how you phased out and deprecated a beloved but unprofitable legacy feature without alienating core customers."},
        {"category": "Pricing & Monetization", "text": "Tell me about an initiative where you analyzed customer willingness to pay and designed a new pricing tier or monetization model."},
        {"category": "Cross-Functional Friction", "text": "Describe a project where engineering and design had conflicting visions on technical feasibility vs UI delight. How did you unify them?"},
        {"category": "North Star & OKRs", "text": "How do you establish a North Star metric and cascade actionable quarterly OKRs down to cross-functional squads?"},
        {"category": "Competitive Response", "text": "How do you respond when a direct competitor unexpectedly launches a flagship feature that threatens your market share?"},
        {"category": "User Onboarding Funnel", "text": "Tell me about a time you optimized a complex onboarding flow to boost day-1 and day-7 user activation."},
        {"category": "Technical Debt Advocacy", "text": "How do you justify and communicate the business ROI of architectural refactoring to non-technical business stakeholders?"},
        {"category": "Product-Market Fit", "text": "What leading and lagging indicators do you track to validate whether a zero-to-one product has achieved true Product-Market Fit?"},
        {"category": "Data vs Intuition", "text": "Describe a pivotal product decision where the quantitative data was inconclusive, and you had to rely on customer empathy and strategic instinct."}
    ],
    "DevOps / Cloud Engineer": [
        {"category": "CI/CD & Automation", "text": "How do you design a zero-downtime deployment pipeline with automated canary testing and rollback mechanisms?"},
        {"category": "Incident Management", "text": "Describe how you diagnosed and resolved a major cloud infrastructure outage or network partition."},
        {"category": "Infrastructure as Code", "text": "How do you manage state and avoid drift in a multi-environment Terraform or Kubernetes setup?"},
        {"category": "Security & Compliance", "text": "Walk me through how you secure container images, manage secrets, and enforce least-privilege IAM policies."},
        {"category": "Cost Optimization", "text": "Tell me about an initiative where you analyzed and significantly reduced cloud infrastructure spend without degrading SLA."},
        {"category": "Kubernetes Autoscaling", "text": "How do you configure Horizontal Pod Autoscalers (HPA), Cluster Autoscaler, and Pod Disruption Budgets for spiky production workloads?"},
        {"category": "Secrets Rotation", "text": "Describe how you automated zero-downtime credential and certificate rotation across distributed Kubernetes clusters."},
        {"category": "GitOps Architecture", "text": "What are the architectural advantages and challenges of deploying GitOps (e.g. ArgoCD or Flux) across multi-tenant clusters?"},
        {"category": "Observability & Alert Fatigue", "text": "How do you establish meaningful SLOs/SLAs and tune Prometheus/Datadog alerting thresholds to eliminate on-call alert fatigue?"},
        {"category": "Disaster Recovery Testing", "text": "Walk me through how you planned and executed a live multi-region disaster recovery simulation to verify RTO and RPO."},
        {"category": "Service Mesh & Networking", "text": "When does adopting a service mesh (like Istio or Linkerd) justify its latency and operational complexity in microservices?"},
        {"category": "DDoS & Edge Defense", "text": "Describe how you architected edge protection using Cloudflare/WAF to defend applications against Layer 7 distributed DDoS attacks."},
        {"category": "Chaos Engineering", "text": "Tell me about a chaos engineering experiment you ran to uncover latent failure modes in your infrastructure before they occurred in production."},
        {"category": "Container Image Hardening", "text": "How do you enforce minimal distroless base images, non-root execution, and automated vulnerability gating in CI pipelines?"},
        {"category": "Hybrid Cloud Networking", "text": "Describe how you architected resilient, low-latency cross-region or on-premise cloud interconnects using Transit Gateways and VPNs."}
    ],
    "General": [
        {"category": "Career Motivation", "text": "Walk me through your background and the pivotal career decisions that led you to this role."},
        {"category": "Problem Solving", "text": "Describe the most challenging obstacle you overcame in the last 12 months. What was the outcome?"},
        {"category": "Leadership & Ownership", "text": "Tell me about a time you noticed an organizational or technical problem that was not your responsibility, but you stepped up to solve it."},
        {"category": "Adaptability", "text": "Describe a situation where project priorities completely changed halfway through. How did you adapt?"},
        {"category": "Constructive Feedback", "text": "Tell me about the toughest piece of critical feedback you received and how you actively worked to address it."},
        {"category": "Collaboration Under Pressure", "text": "Tell me about a time you had to collaborate closely with a challenging colleague to deliver a mission-critical project."},
        {"category": "Ambiguity & Initiative", "text": "Describe a time when project specifications were vague or direction was missing. How did you create clarity and drive forward?"},
        {"category": "Learning Velocity", "text": "Tell me about a situation where you had to master an unfamiliar technology or domain in days to meet a high-stakes business goal."},
        {"category": "Professional Integrity", "text": "Describe a situation where you were pressured to cut corners or compromise quality. How did you uphold professional standards?"},
        {"category": "Mentorship & Culture", "text": "How have you actively contributed to improving team culture, knowledge sharing, or mentoring other professionals?"},
        {"category": "Time & Priorities", "text": "When juggling multiple high-stakes deadlines with limited hours, what framework do you use to ruthlessly prioritize?"},
        {"category": "Resilience After Setback", "text": "Describe a major professional failure or missed goal. How did you process it and what structural improvements did you make?"},
        {"category": "Executive Communication", "text": "Tell me about a time you had to deliver difficult news or project delays to executive stakeholders. How did you present the update?"},
        {"category": "Innovation & Optimization", "text": "Describe an everyday workflow inefficiency you noticed and took the initiative to automate or streamline for your organization."},
        {"category": "Long-Term Vision", "text": "Where do you see your technical and leadership contributions evolving over the next three to five years?"}
    ]
}


def questions_for(role: str, count: int = 5, seen_questions: list = None) -> list:
    """Return randomized, non-repeating open-ended STAR interview questions."""
    bank = list(QUESTIONS.get(role, QUESTIONS["General"]))
    seen_set = set(seen_questions or [])
    
    unseen = [q for q in bank if q.get("text") not in seen_set]
    if len(unseen) >= count:
        selected = random.sample(unseen, count)
    else:
        previously_seen = [q for q in bank if q.get("text") in seen_set]
        needed = count - len(unseen)
        filler = random.sample(previously_seen, min(needed, len(previously_seen))) if previously_seen else []
        selected = unseen + filler
        if len(selected) < count:
            selected = (bank * ((count // len(bank)) + 1))[:count]
        random.shuffle(selected)
    return selected


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
                {"id": "A", "text": "B-Trees efficiently support range queries (BETWEEN, >, <) and prefix sorting"},
                {"id": "B", "text": "Hash indexes consume 10x less RAM on SSDs"},
                {"id": "C", "text": "Hash indexes cannot be stored on disk files"},
                {"id": "D", "text": "B-Trees allow O(1) search in the worst case"}
            ],
            "correct": "A",
            "explanation": "Hash indexes only support exact equality matches (=), whereas B+Trees store keys in sorted order, enabling fast range scans, ordering, and prefix matching."
        },
        {
            "category": "Microservices & Distributed Systems",
            "text": "What is the primary role of the Outbox Pattern in microservices architectures?",
            "options": [
                {"id": "A", "text": "To compress outgoing HTTP request bodies before network transmission"},
                {"id": "B", "text": "To guarantee atomic state updates and event publishing without distributed 2PC transactions"},
                {"id": "C", "text": "To automatically encrypt outgoing TLS sockets"},
                {"id": "D", "text": "To redirect incoming malicious DDOS packets to a honeypot"}
            ],
            "correct": "B",
            "explanation": "The Outbox Pattern writes domain changes and outgoing events to the same local database transaction, guaranteeing reliable message publishing."
        },
        {
            "category": "Networking & Protocols",
            "text": "What key architectural advantage does HTTP/2 provide over HTTP/1.1 for web application performance?",
            "options": [
                {"id": "A", "text": "Binary multiplexing over a single TCP connection to eliminate head-of-line blocking at the HTTP layer"},
                {"id": "B", "text": "Complete removal of TCP handshake overhead"},
                {"id": "C", "text": "Built-in automatic AES-256 database encryption"},
                {"id": "D", "text": "Replacing IP addresses with domain hashes"}
            ],
            "correct": "A",
            "explanation": "HTTP/2 multiplexes multiple bidirectional request/response streams across a single TCP connection, preventing HTTP/1.1 head-of-line blocking."
        },
        {
            "category": "Distributed Caching",
            "text": "What is a 'Cache Stampede' (or thundering herd) and what is the best strategy to mitigate it?",
            "options": [
                {"id": "A", "text": "When RAM runs out on the cache server; mitigated by restarting Redis"},
                {"id": "B", "text": "When a hot key expires and hundreds of simultaneous requests overwhelm the database; mitigated by mutual exclusion locks or probabilistic early expiration"},
                {"id": "C", "text": "When invalid JSON crashes the cache parser; mitigated by schema validation"},
                {"id": "D", "text": "When two nodes receive the same IP address; mitigated by DHCP"}
            ],
            "correct": "B",
            "explanation": "A cache stampede occurs when a high-traffic key expires, triggering concurrent expensive DB queries. Mutex locks or XFetch probabilistic refresh mitigate it."
        },
        {
            "category": "System Design & Resiliency",
            "text": "In distributed microservices, what is the primary objective of implementing a Circuit Breaker pattern?",
            "options": [
                {"id": "A", "text": "To prevent cascading failures and give an unhealthy downstream service time to recover"},
                {"id": "B", "text": "To automatically reboot crashing EC2 instances"},
                {"id": "C", "text": "To encrypt payload traffic across Kubernetes namespaces"},
                {"id": "D", "text": "To balance CPU load between primary and replica database instances"}
            ],
            "correct": "A",
            "explanation": "A circuit breaker halts calls to a failing remote dependency once an error threshold is crossed, returning fast fallbacks and preventing resource exhaustion."
        },
        {
            "category": "Algorithms & Optimization",
            "text": "What is the amortized time complexity of inserting n elements into a dynamic array (like Python list or C++ std::vector)?",
            "options": [
                {"id": "A", "text": "O(1) amortized time per insertion"},
                {"id": "B", "text": "O(log n) amortized time per insertion"},
                {"id": "C", "text": "O(n) amortized time per insertion"},
                {"id": "D", "text": "O(n log n) amortized time per insertion"}
            ],
            "correct": "A",
            "explanation": "Although doubling the array capacity takes O(n) work during a resize, it happens infrequently enough that the average cost per insertion remains O(1)."
        },
        {
            "category": "Security & Cryptography",
            "text": "When securely storing user passwords in an enterprise database, which cryptographic approach is recommended?",
            "options": [
                {"id": "A", "text": "Use a salted adaptive key derivation function like Argon2id or bcrypt with appropriate work factors"},
                {"id": "B", "text": "Encrypt passwords using symmetric AES-256 with an environment variable key"},
                {"id": "C", "text": "Hash passwords using un-salted SHA-256 for rapid query lookups"},
                {"id": "D", "text": "Encode passwords with Base64 and store them in an encrypted SSD"}
            ],
            "correct": "A",
            "explanation": "Adaptive hashing algorithms like Argon2id and bcrypt use unique salts and configurable computational cost, rendering offline GPU/rainbow-table cracking infeasible."
        }
    ],
    "Frontend Developer": [
        {
            "category": "Core Web Vitals",
            "text": "Which metric measures the visual stability of a webpage and prevents unexpected content jumps during user interaction?",
            "options": [
                {"id": "A", "text": "Cumulative Layout Shift (CLS)"},
                {"id": "B", "text": "Largest Contentful Paint (LCP)"},
                {"id": "C", "text": "First Input Delay (FID)"},
                {"id": "D", "text": "Interaction to Next Paint (INP)"}
            ],
            "correct": "A",
            "explanation": "CLS measures unexpected layout shifts of visible page elements during loading, maintaining visual stability."
        },
        {
            "category": "React Internals & Optimization",
            "text": "When optimizing a React component using React.memo, what type of comparison is performed by default on incoming props?",
            "options": [
                {"id": "A", "text": "Shallow equality comparison (Object.is) on prop references"},
                {"id": "B", "text": "Deep recursive property traversal"},
                {"id": "C", "text": "JSON stringification comparison"},
                {"id": "D", "text": "Component DOM subtree diffing"}
            ],
            "correct": "A",
            "explanation": "React.memo defaults to shallow prop equality comparison. Passing inline functions or new object literals triggers unnecessary re-renders."
        },
        {
            "category": "Browser Rendering Engine",
            "text": "Which CSS property modifications trigger only GPU Compositing without causing expensive Layout (Reflow) and Paint cycles?",
            "options": [
                {"id": "A", "text": "transform and opacity"},
                {"id": "B", "text": "width and height"},
                {"id": "C", "text": "top and left"},
                {"id": "D", "text": "padding and margin"}
            ],
            "correct": "A",
            "explanation": "Transform and opacity changes are handled directly on the compositor thread on the GPU, avoiding expensive layout and paint calculations."
        },
        {
            "category": "Web Security",
            "text": "What is the most secure cookie configuration for storing authentication session tokens in a Single Page App?",
            "options": [
                {"id": "A", "text": "HttpOnly, Secure, SameSite=Strict (or Lax)"},
                {"id": "B", "text": "Browser LocalStorage accessed via document.cookie"},
                {"id": "C", "text": "SessionStorage without SameSite headers"},
                {"id": "D", "text": "Plain cookies accessible to client JavaScript for AJAX convenience"}
            ],
            "correct": "A",
            "explanation": "HttpOnly prevents JavaScript access (mitigating XSS theft), Secure enforces HTTPS, and SameSite prevents Cross-Site Request Forgery (CSRF)."
        },
        {
            "category": "Modern JavaScript & Bundling",
            "text": "What does Tree Shaking achieve in modern bundlers like Webpack, Rollup, and Vite?",
            "options": [
                {"id": "A", "text": "Eliminating dead or unreferenced exports from the final production bundle using static ES module analysis"},
                {"id": "B", "text": "Compressing PNG images into WebP format"},
                {"id": "C", "text": "Converting synchronous code into async/await"},
                {"id": "D", "text": "Scrambling code to prevent reverse engineering"}
            ],
            "correct": "A",
            "explanation": "Tree shaking relies on the static structure of ES2015 import/export syntax to detect and remove unused code from production bundles."
        },
        {
            "category": "Web Accessibility (WCAG)",
            "text": "When creating a custom accessible modal dialog, which keyboard accessibility requirement is mandatory?",
            "options": [
                {"id": "A", "text": "Trap focus inside the modal and allow dismissal with the Escape key"},
                {"id": "B", "text": "Allow tab key to navigate to underlying page links"},
                {"id": "C", "text": "Disable all ARIA labels to prevent screen reader confusion"},
                {"id": "D", "text": "Force full screen view on all mobile browsers"}
            ],
            "correct": "A",
            "explanation": "Accessible modals must trap focus inside their boundary while open, prevent background interaction, and close gracefully on Escape."
        },
        {
            "category": "Service Workers & PWA",
            "text": "What is the primary architectural restriction placed on Service Workers running in the browser?",
            "options": [
                {"id": "A", "text": "They run on a separate background thread and have zero direct access to the DOM"},
                {"id": "B", "text": "They cannot make fetch requests over HTTPS"},
                {"id": "C", "text": "They can only execute during active user mouse clicks"},
                {"id": "D", "text": "They expire automatically every 10 seconds"}
            ],
            "correct": "A",
            "explanation": "Service Workers run on an isolated worker thread with no DOM access, communicating with web pages via postMessage and caching network requests."
        },
        {
            "category": "Hydration & SSR",
            "text": "What causes a 'Hydration Mismatch' error in SSR frameworks like Next.js or Nuxt?",
            "options": [
                {"id": "A", "text": "The initial server-rendered HTML tree differs from the component tree generated on the first client render"},
                {"id": "B", "text": "The database query took longer than 5 seconds on the server"},
                {"id": "C", "text": "The CSS stylesheet failed to download over CDN"},
                {"id": "D", "text": "The browser has disabled cookie tracking"}
            ],
            "correct": "A",
            "explanation": "Hydration occurs when client JavaScript attaches event handlers to server HTML. Discrepancies (like window.innerWidth or random dates) trigger mismatch errors."
        }
    ],
    "Backend Developer": [
        {
            "category": "Database Consistency",
            "text": "Under the ACID transaction model, which isolation level guarantees protection against Dirty Reads, Non-Repeatable Reads, and Phantom Reads?",
            "options": [
                {"id": "A", "text": "Serializable"},
                {"id": "B", "text": "Repeatable Read"},
                {"id": "C", "text": "Read Committed"},
                {"id": "D", "text": "Read Uncommitted"}
            ],
            "correct": "A",
            "explanation": "Serializable is the highest isolation level. It executes transactions concurrently in a manner equivalent to serial sequential execution."
        },
        {
            "category": "Distributed Consensus",
            "text": "In distributed systems, which protocol is specifically designed to achieve leader election and replicated log consensus across fault-tolerant clusters?",
            "options": [
                {"id": "A", "text": "Raft / Paxos"},
                {"id": "B", "text": "HTTP/3 over UDP"},
                {"id": "C", "text": "SNMP v3"},
                {"id": "D", "text": "OAuth 2.0 PKCE"}
            ],
            "correct": "A",
            "explanation": "Raft and Paxos are consensus algorithms that ensure a cluster of distributed nodes agree on replicated state logs despite node crashes or partitions."
        },
        {
            "category": "Database Indexing & Performance",
            "text": "What is an index 'Covering Query' in relational databases like PostgreSQL or MySQL?",
            "options": [
                {"id": "A", "text": "A query whose requested columns are all present directly in the index, eliminating the need to read the table data pages"},
                {"id": "B", "text": "A query that deletes unused indexes on startup"},
                {"id": "C", "text": "A query that locks all table rows for write updates"},
                {"id": "D", "text": "A query executed purely in the Redis caching layer"}
            ],
            "correct": "A",
            "explanation": "An index covers a query when all SELECT, WHERE, and ORDER BY columns reside in the index itself, avoiding expensive disk I/O to read raw table heap pages."
        },
        {
            "category": "Event Streaming & Queues",
            "text": "In Apache Kafka, what determines the maximum number of consumer instances that can actively read in parallel within a single Consumer Group?",
            "options": [
                {"id": "A", "text": "The total number of Partitions assigned to the subscribed topic"},
                {"id": "B", "text": "The total RAM available on the ZooKeeper / KRaft quorum"},
                {"id": "C", "text": "The network bandwidth limit on the Kafka broker"},
                {"id": "D", "text": "Kafka allows infinite parallel consumers per partition"}
            ],
            "correct": "A",
            "explanation": "Within a consumer group, each partition can be consumed by at most one consumer instance at a time to preserve ordered processing per partition."
        },
        {
            "category": "Distributed Architecture",
            "text": "According to the CAP theorem, when a network partition (P) inevitably occurs in a distributed data store, what trade-off must be made?",
            "options": [
                {"id": "A", "text": "Choose between Consistency (returning errors/waiting) or Availability (returning potentially stale data)"},
                {"id": "B", "text": "Choose between CPU frequency and disk capacity"},
                {"id": "C", "text": "Choose between IPv4 and IPv6"},
                {"id": "D", "text": "Choose between open-source or commercial licensing"}
            ],
            "correct": "A",
            "explanation": "During a network partition, a system can either cancel operations to maintain strict consistency (CP) or respond with local state to stay available (AP)."
        },
        {
            "category": "API Gateway & Rate Limiting",
            "text": "Which algorithm is optimal for rate limiting APIs while allowing smooth burst traffic without memory bloat?",
            "options": [
                {"id": "A", "text": "Token Bucket or Leaky Bucket"},
                {"id": "B", "text": "Bubble Sort"},
                {"id": "C", "text": "Binary Search Tree traversal"},
                {"id": "D", "text": "Round Robin DNS"}
            ],
            "correct": "A",
            "explanation": "The Token Bucket algorithm accumulates tokens at a constant rate and allows bursts up to bucket capacity, providing smooth and memory-efficient throttling."
        },
        {
            "category": "Scalability & Caching",
            "text": "What is the primary danger of the 'Write-Behind' (or write-back) caching pattern?",
            "options": [
                {"id": "A", "text": "Potential data loss if the cache crashes before dirty writes are flushed to persistent database storage"},
                {"id": "B", "text": "High latency on client read operations"},
                {"id": "C", "text": "Inability to store string data types in cache"},
                {"id": "D", "text": "Forced invalidation of the entire database schema"}
            ],
            "correct": "A",
            "explanation": "Write-behind updates cache immediately and delays DB write asynchronously. If the cache node crashes before flushing, uncommitted writes are permanently lost."
        },
        {
            "category": "Security & Architecture",
            "text": "How does the OAuth 2.0 PKCE (Proof Key for Code Exchange) extension prevent authorization code interception attacks?",
            "options": [
                {"id": "A", "text": "By requiring a cryptographically generated code verifier and challenge to redeem the authorization code"},
                {"id": "B", "text": "By requiring clients to store secret keys in public GitHub repos"},
                {"id": "C", "text": "By disabling HTTPS certificates on redirect URLs"},
                {"id": "D", "text": "By replacing bearer tokens with plain text passwords"}
            ],
            "correct": "A",
            "explanation": "PKCE ensures that even if an authorization code is intercepted, the attacker cannot exchange it without the original client code_verifier."
        }
    ],
    "Data Analyst": [
        {
            "category": "Experimentation & Statistics",
            "text": "What does a p-value of 0.03 indicate in a two-tailed A/B test with an alpha threshold of 0.05?",
            "options": [
                {"id": "A", "text": "The observed difference is statistically significant; there is a 3% probability of observing such results assuming the null hypothesis is true"},
                {"id": "B", "text": "There is a 97% chance the feature will fail in production"},
                {"id": "C", "text": "The sample size must be tripled to achieve significance"},
                {"id": "D", "text": "The experiment is completely invalid due to selection bias"}
            ],
            "correct": "A",
            "explanation": "With p < 0.05, we reject the null hypothesis because observing such extreme data purely by chance would happen only 3% of the time."
        },
        {
            "category": "SQL & Analytics",
            "text": "What is the key difference between the RANK() and DENSE_RANK() window functions in SQL?",
            "options": [
                {"id": "A", "text": "RANK() skips subsequent rank numbers after ties (e.g. 1, 2, 2, 4), while DENSE_RANK() does not skip (e.g. 1, 2, 2, 3)"},
                {"id": "B", "text": "RANK() only works on integer columns, while DENSE_RANK() works on text"},
                {"id": "C", "text": "DENSE_RANK() can only be run on partitioned tables"},
                {"id": "D", "text": "RANK() orders ascending, while DENSE_RANK() orders descending"}
            ],
            "correct": "A",
            "explanation": "When duplicate values occur, RANK() produces gaps in the ranking sequence, whereas DENSE_RANK() assigns consecutive rank values."
        },
        {
            "category": "Data Quality & Anomaly Detection",
            "text": "When detecting outliers in skewed, non-normally distributed business data (like customer purchase amounts), which metric is most robust?",
            "options": [
                {"id": "A", "text": "Interquartile Range (IQR) and Median"},
                {"id": "B", "text": "Arithmetic Mean and Standard Deviation"},
                {"id": "C", "text": "Minimum and Maximum values alone"},
                {"id": "D", "text": "Total sum of transactions"}
            ],
            "correct": "A",
            "explanation": "The median and IQR are non-parametric and resistant to extreme outliers, whereas the mean and standard deviation are heavily distorted by skewed tails."
        },
        {
            "category": "Data Modeling",
            "text": "In dimensional data warehousing (Kimball methodology), what is the difference between a Fact table and a Dimension table?",
            "options": [
                {"id": "A", "text": "Fact tables store quantitative business metrics/measurements, while Dimension tables store contextual descriptive attributes"},
                {"id": "B", "text": "Fact tables only contain text, while Dimension tables store numbers"},
                {"id": "C", "text": "Dimension tables must be updated every millisecond"},
                {"id": "D", "text": "Fact tables cannot have foreign keys"}
            ],
            "correct": "A",
            "explanation": "Fact tables contain numerical event measurements (e.g. sales, quantity) and foreign keys referencing descriptive Dimension tables (e.g. customer, product, date)."
        },
        {
            "category": "Cohort Analysis",
            "text": "What does a cohort retention heatmap demonstrate to product leaders?",
            "options": [
                {"id": "A", "text": "How specific user groups acquired in the same time window continue to engage over subsequent days, weeks, or months"},
                {"id": "B", "text": "The temperature of database servers over time"},
                {"id": "C", "text": "The geographical distribution of IP addresses"},
                {"id": "D", "text": "The click-through rate of Google ad campaigns"}
            ],
            "correct": "A",
            "explanation": "Cohort retention analyzes behavioral decay over time across common acquisition cohorts, revealing whether product changes improve long-term user retention."
        },
        {
            "category": "Business Metrics",
            "text": "If customer acquisition cost (CAC) is $200 and customer lifetime value (LTV) is $150, what does this indicate about the business model?",
            "options": [
                {"id": "A", "text": "The business is losing $50 on every customer acquired and has an unsustainable unit economics ratio of 0.75x"},
                {"id": "B", "text": "The business has healthy SaaS margins exceeding 3:1"},
                {"id": "C", "text": "The payback period is under 30 days"},
                {"id": "D", "text": "Marketing spend should be doubled immediately"}
            ],
            "correct": "A",
            "explanation": "When LTV is lower than CAC (LTV:CAC < 1.0), unit economics are negative: the company loses money acquiring customers."
        },
        {
            "category": "Statistical Biases",
            "text": "What is Simpson's Paradox in data analysis?",
            "options": [
                {"id": "A", "text": "A statistical phenomenon where a trend appears in different groups of data but disappears or reverses when the groups are aggregated"},
                {"id": "B", "text": "When machine learning models overfit on training data"},
                {"id": "C", "text": "When null values crash a database query"},
                {"id": "D", "text": "When two variables are perfectly correlated"}
            ],
            "correct": "A",
            "explanation": "Simpson's Paradox occurs when confounding variables distort group comparisons, causing aggregated analysis to draw the exact opposite conclusion of sub-group analysis."
        }
    ],
    "Product Manager": [
        {
            "category": "Prioritization Frameworks",
            "text": "In the RICE scoring framework used for roadmap prioritization, what do the letters R, I, C, and E stand for?",
            "options": [
                {"id": "A", "text": "Reach, Impact, Confidence, and Effort"},
                {"id": "B", "text": "Revenue, Innovation, Cost, and Efficiency"},
                {"id": "C", "text": "Retain, Iterate, Convert, and Expand"},
                {"id": "D", "text": "Risk, Infrastructure, Capacity, and Execution"}
            ],
            "correct": "A",
            "explanation": "RICE evaluates features by multiplying (Reach × Impact × Confidence) divided by Effort, establishing a standardized objective prioritization score."
        },
        {
            "category": "Growth & Retention",
            "text": "Which metric is considered the gold standard indicator of genuine Product-Market Fit (PMF)?",
            "options": [
                {"id": "A", "text": "A retention curve that flattens out parallel to the x-axis over an extended time horizon"},
                {"id": "B", "text": "A high number of total registered user signups in the first month"},
                {"id": "C", "text": "Winning an industry tech award"},
                {"id": "D", "text": "Zero negative customer support tickets"}
            ],
            "correct": "A",
            "explanation": "A retention curve that flattens confirms that a predictable percentage of users find lasting value and never churn, indicating Product-Market Fit."
        },
        {
            "category": "Agile & Delivery",
            "text": "What is the primary distinction between an Output metric and an Outcome metric for product teams?",
            "options": [
                {"id": "A", "text": "Outputs measure what you built (e.g. features shipped), while Outcomes measure customer and business behavior change (e.g. churn reduced)"},
                {"id": "B", "text": "Outputs are tracked by designers, while Outcomes are tracked by marketing"},
                {"id": "C", "text": "Outputs only apply to enterprise sales cycles"},
                {"id": "D", "text": "Outcome metrics cannot be quantified with numbers"}
            ],
            "correct": "A",
            "explanation": "High-performing product organizations focus on outcomes (business/user impact) rather than output velocity (shipping features that nobody uses)."
        },
        {
            "category": "Customer Discovery",
            "text": "According to user research best practices (e.g. 'The Mom Test'), what is the best type of question to ask in customer interviews?",
            "options": [
                {"id": "A", "text": "Questions about specific past behavior, current workflows, and real money spent solving the problem"},
                {"id": "B", "text": "Hypothetical questions asking 'Would you buy this feature if we built it for $10?'"},
                {"id": "C", "text": "Pitching your startup vision and asking for their general opinion"},
                {"id": "D", "text": "Asking them to design the software architecture for you"}
            ],
            "correct": "A",
            "explanation": "Hypothetical questions lead to polite lies. Examining concrete past behavior reveals genuine pain points and actual willingness to pay."
        },
        {
            "category": "Go-To-Market & Pricing",
            "text": "What is the core premise of a 'Product-Led Growth' (PLG) go-to-market model?",
            "options": [
                {"id": "A", "text": "The product itself drives customer acquisition, retention, and expansion through self-serve onboarding and virality"},
                {"id": "B", "text": "Hiring a large field sales team to take clients out to steak dinners"},
                {"id": "C", "text": "Spending 80% of budget on TV advertisements"},
                {"id": "D", "text": "Restricting software access to invite-only VIP conferences"}
            ],
            "correct": "A",
            "explanation": "PLG relies on the product experience itself (freemium/free trial, frictionless self-serve activation) to fuel viral distribution and revenue expansion."
        },
        {
            "category": "Experimentation",
            "text": "When running an A/B test on a core checkout flow, why is 'peeking' at test results daily and stopping early as soon as p < 0.05 dangerous?",
            "options": [
                {"id": "A", "text": "It drastically inflates the False Positive rate (Type I error), leading teams to ship ineffective or harmful features"},
                {"id": "B", "text": "It slows down the database query speed"},
                {"id": "C", "text": "It violates Google search SEO rankings"},
                {"id": "D", "text": "It forces credit card processors to decline transactions"}
            ],
            "correct": "A",
            "explanation": "Repeated significance testing without sample-size discipline or sequential corrections leads to premature stopping during random noise fluctuations."
        },
        {
            "category": "Strategy & Positioning",
            "text": "What does Hamilton Helmer's '7 Powers' framework define as 'Network Effects'?",
            "options": [
                {"id": "A", "text": "When the value of a product increases for every existing user as additional users join the platform"},
                {"id": "B", "text": "Having high-speed fiber optic internet in your headquarters"},
                {"id": "C", "text": "Offering discounts for high volume enterprise purchases"},
                {"id": "D", "text": "Filing utility patents on hardware components"}
            ],
            "correct": "A",
            "explanation": "Network effects create defensible moats because a platform becomes exponentially more useful as user density increases (e.g. marketplaces, social platforms)."
        }
    ],
    "DevOps / Cloud Engineer": [
        {
            "category": "Container Orchestration",
            "text": "In Kubernetes, which controller is best suited for deploying stateless web service replicas that scale based on CPU/memory utilization?",
            "options": [
                {"id": "A", "text": "Deployment (managing a ReplicaSet)"},
                {"id": "B", "text": "DaemonSet"},
                {"id": "C", "text": "StatefulSet"},
                {"id": "D", "text": "Job / CronJob"}
            ],
            "correct": "A",
            "explanation": "Deployments provide declarative updates for Pods and ReplicaSets, ideal for scaling stateless web microservices horizontally."
        },
        {
            "category": "Infrastructure as Code",
            "text": "What is the primary danger of managing Terraform state without a state locking mechanism (like DynamoDB with AWS S3)?",
            "options": [
                {"id": "A", "text": "Concurrent terraform apply executions can corrupt the state file or provision duplicate conflicting resources"},
                {"id": "B", "text": "Terraform code will automatically convert into CloudFormation"},
                {"id": "C", "text": "AWS charges triple rates for unlocked state files"},
                {"id": "D", "text": "Terraform plans will fail to parse HCL syntax"}
            ],
            "correct": "A",
            "explanation": "State locking guarantees exclusive access during plan/apply executions, preventing simultaneous runs from overwriting and corrupting cloud state."
        },
        {
            "category": "Deployment Strategies",
            "text": "What is the key difference between Blue/Green deployment and Canary deployment?",
            "options": [
                {"id": "A", "text": "Blue/Green switches 100% of traffic between two identical environments, while Canary gradually rolls out traffic to a small percentage of users"},
                {"id": "B", "text": "Blue/Green requires Kubernetes, while Canary only works on bare metal"},
                {"id": "C", "text": "Canary deployments cannot be rolled back"},
                {"id": "D", "text": "Blue/Green deployment requires changing the domain name"}
            ],
            "correct": "A",
            "explanation": "Blue/Green maintains two complete production environments and flips traffic all at once. Canary routes a tiny fraction of live traffic (e.g. 5%) to validate stability first."
        },
        {
            "category": "Cloud Security",
            "text": "Which security principle dictates that every service, container, and human user should only be granted the minimum permissions necessary to perform their specific function?",
            "options": [
                {"id": "A", "text": "Principle of Least Privilege (PoLP)"},
                {"id": "B", "text": "Security through Obscurity"},
                {"id": "C", "text": "Defense in Isolation"},
                {"id": "D", "text": "Zero Port Policy"}
            ],
            "correct": "A",
            "explanation": "The Principle of Least Privilege limits IAM permissions strictly to required resources and actions, drastically reducing blast radius if credentials are compromised."
        },
        {
            "category": "Site Reliability Engineering (SRE)",
            "text": "What is an 'Error Budget' in Google SRE methodology?",
            "options": [
                {"id": "A", "text": "The allowable room for unreliability (100% minus SLO), defining how much downtime or errors a service can incur before feature releases are halted"},
                {"id": "B", "text": "The monetary fine paid to clients when an outage occurs"},
                {"id": "C", "text": "The annual hardware budget allocated to replace faulty hard drives"},
                {"id": "D", "text": "The maximum number of bugs allowed in a Jira sprint"}
            ],
            "correct": "A",
            "explanation": "An error budget represents 100% - SLO (e.g. 0.1% for a 99.9% SLO). It creates balanced alignment between product release velocity and engineering reliability."
        },
        {
            "category": "Networking & DNS",
            "text": "Why do web browsers and operating systems implement DNS Time To Live (TTL)?",
            "options": [
                {"id": "A", "text": "To cache DNS query resolution records and prevent repeated round-trip lookups to authoritative nameservers"},
                {"id": "B", "text": "To encrypt DNS packets with SSL certificates"},
                {"id": "C", "text": "To prevent users from visiting expired domains"},
                {"id": "D", "text": "To dynamically change IP addresses on every packet"}
            ],
            "correct": "A",
            "explanation": "DNS TTL defines the duration intermediate resolvers and clients may cache a DNS record before re-querying the authoritative nameserver."
        },
        {
            "category": "Kubernetes Storage",
            "text": "What is the role of a Kubernetes StorageClass?",
            "options": [
                {"id": "A", "text": "To enable dynamic provisioning of underlying cloud storage volumes (like AWS EBS or GCP Persistent Disks) when a PVC is created"},
                {"id": "B", "text": "To compress Docker container images in local memory"},
                {"id": "C", "text": "To store environment variables inside etcd"},
                {"id": "D", "text": "To encrypt Kubernetes Secret objects"}
            ],
            "correct": "A",
            "explanation": "StorageClasses define provisioners and parameters for dynamic volume creation, abstracting underlying cloud storage from developers."
        }
    ],
    "General": [
        {
            "category": "STAR Methodology",
            "text": "In the STAR interview response framework, which section should command the majority of your time and detail?",
            "options": [
                {"id": "A", "text": "Action: The specific technical and leadership actions YOU took to solve the challenge"},
                {"id": "B", "text": "Situation: Spending 10 minutes giving lengthy company background"},
                {"id": "C", "text": "Task: Explaining why your manager assigned the work to you"},
                {"id": "D", "text": "Result: Stating that everyone was happy without metrics"}
            ],
            "correct": "A",
            "explanation": "Interviewers evaluate your personal capability and decision making. Dedicate 60%+ of your answer to concrete Actions you executed."
        },
        {
            "category": "Workplace Communication",
            "text": "When communicating an unexpected project delay to executive stakeholders, what is the best approach?",
            "options": [
                {"id": "A", "text": "Proactively alert them as early as possible, clearly explain root cause, outline mitigation options, and present a revised timeline"},
                {"id": "B", "text": "Wait until the exact launch day to mention that the project is not ready"},
                {"id": "C", "text": "Blame another team publicly in a meeting to deflect responsibility"},
                {"id": "D", "text": "Ship incomplete, broken code quietly and fix it later in secret"}
            ],
            "correct": "A",
            "explanation": "Early, proactive communication demonstrates executive maturity, builds stakeholder trust, and gives the business time to adjust dependencies."
        },
        {
            "category": "Agile & Continuous Improvement",
            "text": "In Scrum methodology, what is the dedicated purpose of the Sprint Retrospective meeting?",
            "options": [
                {"id": "A", "text": "For the team to inspect their own workflow, processes, and teamwork, and agree on actionable improvements for the next sprint"},
                {"id": "B", "text": "To demo completed software features to external end-users and investors"},
                {"id": "C", "text": "To perform quarterly individual employee compensation evaluations"},
                {"id": "D", "text": "To assign daily Jira story points for the upcoming 6 months"}
            ],
            "correct": "A",
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
                {"id": "A", "text": "Quadrant 2: Not Urgent but Highly Important (Strategic planning, refactoring, learning, relationships)"},
                {"id": "B", "text": "Quadrant 1: Urgent and Important (Immediate crises)"},
                {"id": "C", "text": "Quadrant 3: Urgent but Not Important (Constant interruptions and trivial requests)"},
                {"id": "D", "text": "Quadrant 4: Not Urgent and Not Important (Time-wasting busywork)"}
            ],
            "correct": "A",
            "explanation": "Investing time in Quadrant 2 (Not Urgent, but Important) prevents problems before they become emergency crises (Quadrant 1), driving sustained high performance."
        },
        {
            "category": "Ownership & Accountability",
            "text": "When an engineer discovers a defect that escaped into production because of their own oversight, what demonstrates extreme ownership?",
            "options": [
                {"id": "A", "text": "Acknowledge the mistake transparently, coordinate the rollback/hotfix, write a blameless postmortem, and add automated tests to prevent recurrence"},
                {"id": "B", "text": "Quietly force-push over git history to hide the commit"},
                {"id": "C", "text": "Blame the QA engineer for not catching it during testing"},
                {"id": "D", "text": "Pretend the bug was an undocumented feature requested by customers"}
            ],
            "correct": "A",
            "explanation": "Extreme ownership involves taking complete responsibility, remediating the immediate issue, and engineering systemic prevention."
        }
    ]
}


def mcq_questions_for(role: str, count: int = 5, seen_questions: list = None) -> list:
    """Return randomized, non-repeating multiple choice technical interview questions."""
    bank = list(MCQ_QUESTIONS.get(role, MCQ_QUESTIONS["General"]))
    seen_set = set(seen_questions or [])
    
    unseen = [q for q in bank if q.get("text") not in seen_set]
    if len(unseen) >= count:
        selected = random.sample(unseen, count)
    else:
        previously_seen = [q for q in bank if q.get("text") in seen_set]
        needed = count - len(unseen)
        filler = random.sample(previously_seen, min(needed, len(previously_seen))) if previously_seen else []
        selected = unseen + filler
        if len(selected) < count:
            selected = (bank * ((count // len(bank)) + 1))[:count]
        random.shuffle(selected)
    return selected


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
            "word_count": word_count,
            "star": {"situation": False, "task": False, "action": False, "result": False},
            "strengths": [],
            "improvements": ["Provide a detailed response addressing the situation, task, action, and result."],
            "feedback": "Your answer was too short to evaluate. Please elaborate using the STAR method."
        }

    # First attempt AI evaluation via Gemini
    try:
        from ai.gemini_client import gemini_assess_interview
        gemini_result = gemini_assess_interview(text, question)
        if gemini_result and "score" in gemini_result and "star" in gemini_result:
            return gemini_result
    except Exception:
        pass

    # Heuristic STAR assessment fallback
    text_lower = text.lower()
    has_situation = any(k in text_lower for k in STAR_KEYWORDS["situation"])
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
