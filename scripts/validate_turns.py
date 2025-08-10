#!/usr/bin/env python3
import json
import jsonlines
from pathlib import Path
from collections import defaultdict, Counter
import statistics

PROCESSED = Path('data/processed')
TURNS_FILE = PROCESSED / 'turns' / 'turns.jsonl'
TURN_EMB_FILE = PROCESSED / 'turns' / 'turn_embeddings.jsonl'


def pct(x, total):
    return 0.0 if total == 0 else (100.0 * x / total)


def main():
    if not TURNS_FILE.exists():
        print(f"Missing {TURNS_FILE}")
        return

    # Load turns
    turns = []
    with jsonlines.open(TURNS_FILE) as reader:
        for t in reader:
            turns.append(t)

    total = len(turns)
    chats = set(t.get('chat_id') for t in turns)
    per_chat = defaultdict(int)
    for t in turns:
        per_chat[t.get('chat_id')] += 1

    both_sides = 0
    only_user = 0
    only_assistant = 0
    empty_both = 0
    unknown_roles = 0
    summaries = []
    long_summaries = 0
    missing_ts = 0

    # Validate monotonic turn_ids per chat and prev_turn_ids
    monotonic_ok = True
    prev_ok = True
    by_chat = defaultdict(list)
    for t in turns:
        by_chat[t.get('chat_id')].append(t)

    for chat_id, items in by_chat.items():
        items.sort(key=lambda x: x.get('turn_id', 0))
        # monotonic
        expected = 1
        for it in items:
            if it.get('turn_id') != expected:
                monotonic_ok = False
                break
            expected += 1
        # prev_turn_ids coverage
        for it in items:
            tid = it.get('turn_id', 0)
            prev_ids = it.get('prev_turn_ids', [])
            for pid in prev_ids:
                if pid < 1 or pid >= tid:
                    prev_ok = False
                    break

    for t in turns:
        user = (t.get('text_user') or '').strip()
        asst = (t.get('text_assistant') or '').strip()
        roles = t.get('roles', [])
        if 'user' not in roles or 'assistant' not in roles:
            unknown_roles += 1
        if user and asst:
            both_sides += 1
        elif user and not asst:
            only_user += 1
        elif asst and not user:
            only_assistant += 1
        else:
            empty_both += 1
        s = (t.get('summary') or '').strip()
        summaries.append(len(s))
        if len(s) > 240:
            long_summaries += 1
        if t.get('ts') in (None, ''):
            missing_ts += 1

    # Embeddings coverage and dim
    emb_total = 0
    emb_dim_counts = Counter()
    emb_uids = set()
    if TURN_EMB_FILE.exists():
        with jsonlines.open(TURN_EMB_FILE) as reader:
            for rec in reader:
                emb_total += 1
                vec = rec.get('embedding', [])
                emb_dim_counts[len(vec)] += 1
                emb_uids.add(rec.get('turn_uid'))

    # Print stats
    print("\nTurnization Stats")
    print("================")
    print(f"Total turns: {total}")
    print(f"Unique chats: {len(chats)}")
    if per_chat:
        vals = list(per_chat.values())
        print(f"Turns per chat — avg: {statistics.mean(vals):.1f}, median: {statistics.median(vals):.1f}, p95: {statistics.quantiles(vals, n=20)[18]:.0f}")
    print(f"Both sides present: {both_sides} ({pct(both_sides, total):.1f}%)")
    print(f"Only user: {only_user} ({pct(only_user, total):.1f}%)")
    print(f"Only assistant: {only_assistant} ({pct(only_assistant, total):.1f}%)")
    print(f"Empty both: {empty_both} ({pct(empty_both, total):.1f}%)")
    print(f"Missing ts: {missing_ts} ({pct(missing_ts, total):.1f}%)")
    print(f"Monotonic turn_ids per chat: {monotonic_ok}")
    print(f"prev_turn_ids valid: {prev_ok}")

    if summaries:
        print("\nSummary Lengths (chars)")
        print("-----------------------")
        print(f"avg: {statistics.mean(summaries):.1f}, median: {statistics.median(summaries):.1f}, p95: {statistics.quantiles(summaries, n=20)[18]:.0f}")
        print(f">240 chars: {long_summaries} ({pct(long_summaries, total):.1f}%)")

    print("\nEmbedding Coverage")
    print("------------------")
    print(f"Embeddings total: {emb_total} (coverage: {pct(emb_total, total):.1f}% of turns)")
    if emb_dim_counts:
        print(f"Vector dims distribution: {dict(emb_dim_counts)}")
    missing_embeddings = total - emb_total
    if missing_embeddings:
        print(f"Missing embeddings for {missing_embeddings} turns")

    # Sample potential issues
    print("\nSamples")
    print("-------")
    # Empty assistant examples
    shown = 0
    for t in turns:
        if (t.get('text_user') or '').strip() and not (t.get('text_assistant') or '').strip():
            print("Empty assistant example:")
            print(json.dumps({k: t[k] for k in ['turn_uid','summary','text_user','text_assistant'] if k in t}, ensure_ascii=False)[:600])
            shown += 1
            if shown >= 2:
                break

    shown = 0
    for t in turns:
        s = (t.get('summary') or '')
        if len(s) > 300:
            print("Long summary example (>300 chars):")
            print(json.dumps({k: t[k] for k in ['turn_uid','summary'] if k in t}, ensure_ascii=False)[:600])
            shown += 1
            if shown >= 2:
                break


if __name__ == '__main__':
    main() 