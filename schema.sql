CREATE TABLE IF NOT EXISTS perspective (
    ch_id BIGINT PRIMARY KEY,
    server_id BIGINT NOT NULL,
    log_ch_id BIGINT NOT NULL
);

CREATE TABLE IF NOT EXISTS reputation (
    server_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    rep int
);

CREATE TABLE IF NOT EXISTS afk (
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    reason TEXT,
    PRIMARY KEY (user_id, guild_id)
);

CREATE TABLE IF NOT EXISTS message_log (
    server_id BIGINT PRIMARY KEY,
    log_channel BIGINT
);