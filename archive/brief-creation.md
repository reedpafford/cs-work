# RUNBOOK — Brief creation in Notion
> Trigger: "make RP##" · "new brief" · "create RP##". Output: a brief page in Create with ONE Variations DB and ONE V1, Format set, nothing else filled. Stop and wait.
> Sources mined: no-duplicate-variations-db · variation-template-vs-page · brief-finalize-sop · style-taxonomy.

> 🚨 Before any write: fetch the current page. Reed's manual edits override my plan. If a line I meant to change was edited by him, ask first.

## The call (this is 90% of the runbook)
```
notion-create-pages
  parent:      { type: data_source_id, data_source_id: 278b1be2-c8a2-80ab-8315-000bbbe99f43 }   # Create
  template_id: 2eeb1be2-c8a2-80e8-bc18-d125a831b4a3                                             # brief template — creates the Variations DB AND V1
  properties:  { Brief: "RP##", Format: ["3a5b1be2-c8a2-80bc-b5a3-d04e72bc9bc0"] }              # Format = Authority unless Reed names another (property renamed from Style, 2026-09-16)
```
Pass `template_id` ONCE. Never `apply_template` after it. Never create a V1 yourself.

## Steps
1. **Next number.** Query Create for the highest `RP` Brief. Verify it individually, never trust one search. (CM28) Never go off memory or CLAUDE.md's "next brief" line: Reed creates briefs himself between turns. (JC21, 2026-09-14: I created a duplicate eight minutes after his; he deleted mine.) If the query is rate-limited, `notion-search` the number first.
2. **Create** with the call above. Format relation set at creation: Authority `3a5b1be2-c8a2-80bc-b5a3-d04e72bc9bc0` · Animation `373b1be2-c8a2-8029-bc4b-f17098cb0037` · LFS `36eb1be2-c8a2-80a2-b744-d847a5fbb5cf` · Reaction `3d7b1be2-c8a2-8037-92d0-c0c41769d8f2` · Podcast `3d7b1be2-c8a2-80ce-930a-d9bf443906a2` · UGC `3dcb1be2-c8a2-807d-994a-cd338097fbb7` (a creator's own video, not one of our personas). A RP brief with Format blank is a defect.
3. **Fetch the brief.** Read the inline `<database … data-source-url="collection://…">Variations</database>` tag. That collection ID is where V1 lives.
4. **Query that Variations DS** (rows mode). Expect exactly one row, `V1`. Open it. It has three callouts: Text Hook · Script · Page/Primary Text.
5. **Fill V1** with `update_content`, anchoring on the callout labels. Script goes after `**Script**`; hook line first, then body, one beat per line. Leave Text Hook empty (Reed writes it). Leave Page/Primary Text empty (finalize fills them).
   **LFS brief (Format = LFS):** delete the whole Text Hook callout and delete the `**Primary Text:**` line from the third callout, leaving `**Page:** Palace Guard`. The Script callout holds the entire post (scan it with `--lfs`). Two callouts, nothing else. (Reed, 2026-09-16)
6. **Stop.** Status stays Ideation. First Line, Name, Awareness, Angle, Product, Lander, Hypothesis, Variables all stay blank until "finalize."

## The three traps (each has burned a brief)
- **Notion's "default template" never fires on an API create; only `template_id` does, and it lands in the background (JC42, 2026-09-30).** So a blank brief in the first minutes is normal, not a failure. Tell Reed in one line "template's loading, don't apply it by hand," because his manual apply on top of mine made a second Variations DB. On the first JC42 I re-applied at 3½ minutes on a cached blank (every fetch said the same `as of`), broke my own rule, and he deleted the brief.
- **Blank page where `page_last_edited_at` still equals `Created time` to the millisecond after five minutes = the template never applied (JC29, 2026-09-16).** On a real application the last-edit stamp moves a second or two past creation (JC28). In that exact case one `apply_template` with the brief template is right, then fetch until the Variations database shows. It applied cleanly, one DB, no duplicate. Same on JC30 and JC31 (2026-09-17): three briefs running, so expect it; create, wait the five minutes, apply once.
- **Blank page after create = CACHE, not failure.** If two consecutive fetches show the same `as of` timestamp, you are reading cache. Do NOT re-apply the template. Run `sleep 120` in the background, re-fetch. Only a FRESH-timestamped blank fetch earns one `apply_template` retry. (JC17, 2026-09-09: re-applied on cache → duplicate Variations DB.)
- **Duplicate Variations DB anyway?** Use the FIRST listed one, give Reed the URL of the second to delete in the UI (no delete tool), never write to both.
- **A page titled bare `V` is the DS template.** Never write to it. Real pages are `V1`, `V2`, `V3`. (JK106)

## Never
- Create a brief without `template_id` then wait for V1 "to appear." It won't. (JK215)
- Write Hypothesis, Variables, Editor, or flip Status at creation. (JK120)
- Put notes, placeholders, or a "diff convention" line on the page. Decisions stay in chat.
