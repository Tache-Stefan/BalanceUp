BEGIN;


-- =========================================================
-- 1. ENUM TYPES
-- =========================================================

CREATE TYPE user_role AS ENUM (
    'user',
    'moderator',
    'admin'
);

CREATE TYPE verification_status AS ENUM (
    'pending',
    'approved',
    'rejected'
);

CREATE TYPE category_type AS ENUM (
    'income',
    'expense'
);

CREATE TYPE goal_status AS ENUM (
    'active',
    'achieved',
    'cancelled'
);

CREATE TYPE challenge_status AS ENUM (
    'active',
    'completed',
    'failed'
);

CREATE TYPE badge_criteria AS ENUM (
    'points',
    'streak_days',
    'challenges_completed'
);

CREATE TYPE points_reason AS ENUM (
    'monthly_budget',
    'challenge_completed',
    'reversal',
    'admin_adjustment'
);

CREATE TYPE article_status AS ENUM (
    'draft',
    'published'
);

CREATE TYPE consultation_status AS ENUM (
    'pending',
    'awaiting_payment',
    'confirmed',
    'completed',
    'rejected',
    'cancelled'
);

CREATE TYPE payment_status AS ENUM (
    'pending',
    'succeeded',
    'failed',
    'refunded'
);


-- =========================================================
-- 2. USERS
-- =========================================================

CREATE TABLE users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,

    role user_role NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Gamification
    current_streak_days INTEGER NOT NULL DEFAULT 0 CHECK (current_streak_days >= 0),
    last_activity_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_users_email CHECK (email LIKE '%_@_%.__%')
);
CREATE UNIQUE INDEX ux_users_email
ON users (LOWER(email));


-- =========================================================
-- 3. MODERATOR PROFILES
-- =========================================================

CREATE TABLE moderator_profiles (
    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    specialization VARCHAR(150),
    experience_years SMALLINT CHECK (experience_years >= 0),
    accreditation_details TEXT NOT NULL,
    verification_status verification_status NOT NULL DEFAULT 'pending',
    verified_by BIGINT REFERENCES users(id),
    verified_at TIMESTAMPTZ,
    consultation_price NUMERIC(10,2) CHECK (consultation_price > 0),
    consultation_duration_min SMALLINT CHECK (consultation_duration_min > 0),
    availability_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_moderator_verification
    CHECK (
        verification_status <> 'approved'
        OR (
            verified_by IS NOT NULL
            AND verified_at IS NOT NULL
        )
    )
);


-- =========================================================
-- 4. CATEGORIES
-- =========================================================

CREATE TABLE categories (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- NULL = categorie globala
    -- NOT NULL = categorie personala
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(80) NOT NULL,
    type category_type NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ux_categories_global
ON categories (LOWER(name), type)
WHERE user_id IS NULL;

CREATE UNIQUE INDEX ux_categories_personal
ON categories (user_id, LOWER(name), type)
WHERE user_id IS NOT NULL;


-- =========================================================
-- 5. TRANSACTIONS
-- =========================================================

CREATE TABLE transactions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    transaction_date DATE NOT NULL,
    description VARCHAR(255),
    -- Identificarea provenientei tranzactiei
    imported_from_csv BOOLEAN NOT NULL DEFAULT FALSE,
    external_reference_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_transactions_user_date
ON transactions (user_id, transaction_date);

CREATE INDEX ix_transactions_user_category
ON transactions (user_id, category_id);


-- =========================================================
-- 6. MONTHLY BUDGETS
-- =========================================================

CREATE TABLE monthly_budgets (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id BIGINT NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    -- Prima zi a lunii
    month DATE NOT NULL,
    limit_amount NUMERIC(12,2) NOT NULL CHECK (limit_amount > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_budget_month
        CHECK (
            month = DATE_TRUNC('month', month)::DATE
        ),

    CONSTRAINT ux_budget_user_category_month
        UNIQUE (user_id, category_id, month)
);

CREATE INDEX ix_budgets_user_month
ON monthly_budgets (user_id, month);


-- =========================================================
-- 7. SAVINGS GOALS
-- =========================================================

CREATE TABLE savings_goals (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    target_amount NUMERIC(12,2) NOT NULL CHECK (target_amount > 0),
    -- Progresul economisirii
    saved_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (saved_amount >= 0),
    deadline DATE,
    status goal_status NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_savings_goals_user
ON savings_goals (user_id, status);


-- =========================================================
-- 8. CHALLENGES
-- =========================================================

CREATE TABLE challenges (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_by BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    -- NULL = toate categoriile de cheltuieli
    category_id BIGINT REFERENCES categories(id) ON DELETE SET NULL,
    -- 0 = fara cheltuieli
    -- >0 = limita maxima permisa
    max_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (max_amount >= 0),
    duration_days SMALLINT NOT NULL CHECK (duration_days > 0),
    available_from DATE NOT NULL,
    available_until DATE NOT NULL,
    points_reward INTEGER NOT NULL DEFAULT 20 CHECK (points_reward > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	
    CONSTRAINT ck_challenge_dates
        CHECK (available_until >= available_from)
);

CREATE INDEX ix_challenges_available
ON challenges (available_from, available_until);


-- =========================================================
-- 9. USER CHALLENGES
-- =========================================================

CREATE TABLE user_challenges (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id BIGINT NOT NULL REFERENCES challenges(id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ends_at TIMESTAMPTZ NOT NULL,
    status challenge_status NOT NULL DEFAULT 'active',
    finished_at TIMESTAMPTZ,

    CONSTRAINT ux_user_challenge UNIQUE (user_id, challenge_id),
    CONSTRAINT ck_user_challenge_dates CHECK (ends_at > started_at)
);

CREATE INDEX ix_user_challenges_user_status
ON user_challenges (user_id, status);


-- =========================================================
-- 10. BADGES
-- =========================================================

CREATE TABLE badges (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(255),
    criteria_type badge_criteria NOT NULL,
    criteria_value INTEGER NOT NULL CHECK (criteria_value > 0),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);


-- =========================================================
-- 11. USER BADGES
-- =========================================================

CREATE TABLE user_badges (
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id BIGINT NOT NULL REFERENCES badges(id) ON DELETE RESTRICT,
    awarded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, badge_id)
);


-- =========================================================
-- 12. POINTS LEDGER
-- =========================================================

CREATE TABLE points_ledger (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    points_delta INTEGER NOT NULL CHECK (points_delta <> 0),
    reason points_reason NOT NULL,
    -- Luna recompensata
    period_month DATE,
    -- Provocarea recompensata
    user_challenge_id BIGINT REFERENCES user_challenges(id) ON DELETE RESTRICT,
    -- Recompensa anulata
    reversal_of_id BIGINT REFERENCES points_ledger(id) ON DELETE RESTRICT,
    note VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_points_month
        CHECK (
            period_month IS NULL
            OR period_month =
                DATE_TRUNC('month', period_month)::DATE
        ),

    CONSTRAINT ck_points_reason
        CHECK (
            (
                reason = 'monthly_budget'
                AND period_month IS NOT NULL
                AND points_delta > 0
            )
            OR
            (
                reason = 'challenge_completed'
                AND user_challenge_id IS NOT NULL
                AND points_delta > 0
            )
            OR
            (
                reason = 'reversal'
                AND reversal_of_id IS NOT NULL
                AND points_delta < 0
            )
            OR
            (
                reason = 'admin_adjustment'
            )
        )
);

-- Previne recompensarea aceleiasi luni de doua ori
CREATE UNIQUE INDEX ux_points_month
ON points_ledger (user_id, period_month)
WHERE reason = 'monthly_budget';

-- Previne recompensarea aceleiasi provocari de doua ori
CREATE UNIQUE INDEX ux_points_challenge
ON points_ledger (user_challenge_id)
WHERE reason = 'challenge_completed';

-- Previne anularea repetata a aceleiasi recompense
CREATE UNIQUE INDEX ux_points_reversal
ON points_ledger (reversal_of_id)
WHERE reason = 'reversal';

CREATE INDEX ix_points_user
ON points_ledger (user_id, created_at);


-- =========================================================
-- 13. ARTICLES
-- =========================================================

CREATE TABLE articles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    status article_status NOT NULL DEFAULT 'draft',
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_article_published
        CHECK (
            status <> 'published'
            OR published_at IS NOT NULL
        )
);

CREATE INDEX ix_articles_status
ON articles (status, published_at);


-- =========================================================
-- 14. CONSULTATION REQUESTS
-- =========================================================

CREATE TABLE consultation_requests (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    moderator_id BIGINT NOT NULL REFERENCES moderator_profiles(user_id) ON DELETE RESTRICT,
    message TEXT NOT NULL,
    status consultation_status NOT NULL DEFAULT 'pending',
    user_contact VARCHAR(255),
    moderator_contact VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    responded_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    CONSTRAINT ck_consultation_not_self
        CHECK (user_id <> moderator_id)
);

CREATE INDEX ix_consultations_user
ON consultation_requests (user_id, status);

CREATE INDEX ix_consultations_moderator
ON consultation_requests (moderator_id, status);


-- =========================================================
-- 15. PAYMENTS
-- =========================================================

CREATE TABLE payments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    consultation_request_id BIGINT NOT NULL REFERENCES consultation_requests(id) ON DELETE RESTRICT,
    provider VARCHAR(40) NOT NULL,
    provider_payment_id VARCHAR(255) UNIQUE,
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL DEFAULT 'EUR',
    status payment_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at TIMESTAMPTZ,
    CONSTRAINT ck_payment_date
        CHECK (
            status NOT IN ('succeeded', 'refunded')
            OR paid_at IS NOT NULL
        )
);

-- O singura plata reusita pentru fiecare consultatie
CREATE UNIQUE INDEX ux_payment_success
ON payments (consultation_request_id)
WHERE status = 'succeeded';

CREATE INDEX ix_payments_consultation
ON payments (consultation_request_id);


-- =========================================================
-- 16. VIEWS
-- =========================================================

-- Totalul punctelor utilizatorului
-- Calculat din istoricul recompenselor

CREATE VIEW v_user_points AS
SELECT
    u.id AS user_id,
    COALESCE(SUM(p.points_delta), 0)::INTEGER
        AS total_points
FROM users u
LEFT JOIN points_ledger p
    ON p.user_id = u.id
GROUP BY u.id;


COMMIT;