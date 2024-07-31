--©2024, Ovais Quraishi
--
-- PostgreSQL database dump
--

-- Dumped from database version 15.7 (Debian 15.7-1.pgdg120+1)
-- Dumped by pg_dump version 15.7 (Debian 15.7-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_cron; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_cron WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION pg_cron; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION pg_cron IS 'Job scheduler for PostgreSQL';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner:
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: schedule_update(); Type: FUNCTION; Schema: public; Owner: rollama
--

CREATE FUNCTION public.schedule_update() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    PERFORM update_row_count();
END; $$;


ALTER FUNCTION public.schedule_update() OWNER TO rollama;

--
-- Name: update_row_count(); Type: FUNCTION; Schema: public; Owner: rollama
--

CREATE FUNCTION public.update_row_count() RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    WITH tbl AS (
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_name NOT LIKE 'pg_%' AND table_schema IN ('public')
    )
    INSERT INTO row_count_history (table_name, row_count)
    SELECT
      table_name,
      (xpath('/row/c/text()',
              query_to_xml(format('SELECT count(*) AS c FROM %I.%I', table_schema, table_name),
                          false,
                          true,
                          '')))[1]::text::int AS rows_n
    FROM tbl ORDER BY 2 DESC;
END; $$;


ALTER FUNCTION public.update_row_count() OWNER TO rollama;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: analysis_documents; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.analysis_documents (
    id integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    shasum_512 text NOT NULL,
    analysis_document jsonb NOT NULL
);


ALTER TABLE public.analysis_documents OWNER TO rollama;

--
-- Name: analysis_documents_id_seq; Type: SEQUENCE; Schema: public; Owner: rollama
--

ALTER TABLE public.analysis_documents ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.analysis_documents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: authors; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.authors (
    author_id character varying NOT NULL,
    author_name character varying,
    author_created_utc integer
);


ALTER TABLE public.authors OWNER TO rollama;

--
-- Name: comments; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.comments (
    comment_id character varying NOT NULL,
    comment_author character varying,
    is_comment_submitter boolean,
    is_comment_edited text,
    comment_created_utc integer,
    comment_body text,
    post_id character varying,
    subreddit text
);


ALTER TABLE public.comments OWNER TO rollama;

--
-- Name: errors; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.errors (
    item_id character varying,
    item_type character varying,
    error text
);


ALTER TABLE public.errors OWNER TO rollama;

--
-- Name: parent_child_tree_data; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.parent_child_tree_data (
    id integer NOT NULL,
    "timestamp" character varying(255),
    shasum256 character varying(255),
    post_id character varying(255),
    parent_child_tree jsonb
);


ALTER TABLE public.parent_child_tree_data OWNER TO rollama;

--
-- Name: parent_child_tree_data_id_seq; Type: SEQUENCE; Schema: public; Owner: rollama
--

CREATE SEQUENCE public.parent_child_tree_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.parent_child_tree_data_id_seq OWNER TO rollama;

--
-- Name: parent_child_tree_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rollama
--

ALTER SEQUENCE public.parent_child_tree_data_id_seq OWNED BY public.parent_child_tree_data.id;


--
-- Name: posts; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.posts (
    post_id character varying NOT NULL,
    subreddit character varying,
    post_author character varying,
    post_title text,
    post_body text,
    post_created_utc integer,
    is_post_oc boolean,
    is_post_video boolean,
    post_upvote_count integer,
    post_downvote_count integer,
    subreddit_members integer
);


ALTER TABLE public.posts OWNER TO rollama;

--
-- Name: row_count_history; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.row_count_history (
    id integer NOT NULL,
    table_name character varying(255),
    row_count integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.row_count_history OWNER TO rollama;

--
-- Name: row_count_history_id_seq; Type: SEQUENCE; Schema: public; Owner: rollama
--

CREATE SEQUENCE public.row_count_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.row_count_history_id_seq OWNER TO rollama;

--
-- Name: row_count_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: rollama
--

ALTER SEQUENCE public.row_count_history_id_seq OWNED BY public.row_count_history.id;


--
-- Name: row_counts_seq; Type: SEQUENCE; Schema: public; Owner: rollama
--

CREATE SEQUENCE public.row_counts_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    MAXVALUE 999999
    CACHE 1;


ALTER TABLE public.row_counts_seq OWNER TO rollama;

--
-- Name: subscription; Type: TABLE; Schema: public; Owner: rollama
--

CREATE TABLE public.subscription (
    datetimesubscribed character varying,
    subreddit character varying
);


ALTER TABLE public.subscription OWNER TO rollama;

--
-- Name: parent_child_tree_data id; Type: DEFAULT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.parent_child_tree_data ALTER COLUMN id SET DEFAULT nextval('public.parent_child_tree_data_id_seq'::regclass);


--
-- Name: row_count_history id; Type: DEFAULT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.row_count_history ALTER COLUMN id SET DEFAULT nextval('public.row_count_history_id_seq'::regclass);


--
-- Name: analysis_documents analysis_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.analysis_documents
    ADD CONSTRAINT analysis_documents_pkey PRIMARY KEY (id);


--
-- Name: analysis_documents analysis_documents_shasum_512_key; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.analysis_documents
    ADD CONSTRAINT analysis_documents_shasum_512_key UNIQUE (shasum_512);


--
-- Name: authors author_pkey; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.authors
    ADD CONSTRAINT author_pkey PRIMARY KEY (author_id);


--
-- Name: comments comment_pkey; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.comments
    ADD CONSTRAINT comment_pkey PRIMARY KEY (comment_id);


--
-- Name: parent_child_tree_data parent_child_tree_data_pkey; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.parent_child_tree_data
    ADD CONSTRAINT parent_child_tree_data_pkey PRIMARY KEY (id);


--
-- Name: parent_child_tree_data parent_child_tree_data_shasum256_key; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.parent_child_tree_data
    ADD CONSTRAINT parent_child_tree_data_shasum256_key UNIQUE (shasum256);


--
-- Name: posts post_pkey; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.posts
    ADD CONSTRAINT post_pkey PRIMARY KEY (post_id);


--
-- Name: row_count_history row_count_history_pkey; Type: CONSTRAINT; Schema: public; Owner: rollama
--

ALTER TABLE ONLY public.row_count_history
    ADD CONSTRAINT row_count_history_pkey PRIMARY KEY (id);


--
-- Name: comment_post_id_idx; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX comment_post_id_idx ON public.comments USING btree (post_id, subreddit);


--
-- Name: errors_item_id_idx; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX errors_item_id_idx ON public.errors USING btree (item_id);


--
-- Name: idx_analysis_documents_comment_id; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_analysis_documents_comment_id ON public.analysis_documents USING btree (((analysis_document ->> 'comment_id'::text)));


--
-- Name: idx_analysis_documents_post_id; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_analysis_documents_post_id ON public.analysis_documents USING btree (((analysis_document ->> 'post_id'::text)));


--
-- Name: idx_analysis_documents_reference_id; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_analysis_documents_reference_id ON public.analysis_documents USING btree (((analysis_document ->> 'reference_id'::text)));


--
-- Name: idx_analysis_documents_reference_id_trunc; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_analysis_documents_reference_id_trunc ON public.analysis_documents USING btree ("left"((analysis_document ->> 'reference_id'::text), 255));


--
-- Name: idx_comments_comment_body_md5; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_comments_comment_body_md5 ON public.comments USING btree (md5(comment_body));


--
-- Name: idx_comments_comment_id; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_comments_comment_id ON public.comments USING btree (comment_id);


--
-- Name: idx_parent_child_tree; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_parent_child_tree ON public.parent_child_tree_data USING btree (parent_child_tree);


--
-- Name: idx_post_id; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_post_id ON public.parent_child_tree_data USING btree (post_id);


--
-- Name: idx_posts_analysis_documents_reference_id; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_posts_analysis_documents_reference_id ON public.posts USING btree (post_id);


--
-- Name: idx_posts_post_id; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX idx_posts_post_id ON public.posts USING btree (post_id);


--
-- Name: post_post_author_idx; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX post_post_author_idx ON public.posts USING btree (post_author);


--
-- Name: post_subreddit_idx; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX post_subreddit_idx ON public.posts USING btree (subreddit);


--
-- Name: shasum_512_index; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX shasum_512_index ON public.analysis_documents USING btree (shasum_512);


--
-- Name: subscription_subreddit_idx; Type: INDEX; Schema: public; Owner: rollama
--

CREATE INDEX subscription_subreddit_idx ON public.subscription USING btree (subreddit);


--
-- Name: SCHEMA cron; Type: ACL; Schema: -; Owner: rollama
--

GRANT ALL ON SCHEMA cron TO rollama;


--
-- Name: FUNCTION schedule_update(); Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON FUNCTION public.schedule_update() TO rollama;


--
-- Name: FUNCTION update_row_count(); Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON FUNCTION public.update_row_count() TO rollama;


--
-- Name: TABLE job; Type: ACL; Schema: cron; Owner: rollama
--

GRANT ALL ON TABLE cron.job TO rollama;


--
-- Name: TABLE job_run_details; Type: ACL; Schema: cron; Owner: rollama
--

GRANT ALL ON TABLE cron.job_run_details TO rollama;


--
-- Name: TABLE analysis_documents; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.analysis_documents TO rollama;


--
-- Name: TABLE authors; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.authors TO rollama;


--
-- Name: TABLE comments; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.comments TO rollama;


--
-- Name: TABLE errors; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.errors TO rollama;


--
-- Name: TABLE parent_child_tree_data; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.parent_child_tree_data TO rollama;


--
-- Name: SEQUENCE parent_child_tree_data_id_seq; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON SEQUENCE public.parent_child_tree_data_id_seq TO rollama;


--
-- Name: TABLE posts; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.posts TO rollama;


--
-- Name: TABLE row_count_history; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.row_count_history TO rollama;


--
-- Name: SEQUENCE row_count_history_id_seq; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON SEQUENCE public.row_count_history_id_seq TO rollama;


--
-- Name: TABLE subscription; Type: ACL; Schema: public; Owner: rollama
--

GRANT ALL ON TABLE public.subscription TO rollama;


--
-- PostgreSQL database dump complete
--
