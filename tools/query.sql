-- Cage Coins social: one read-only query that returns everything plan.py needs.
-- Run it unchanged with the Lovable query_database tool, then save the tool's full JSON result to raw.json.
with last_ev as (select * from events where status = 'completed' order by event_date desc limit 1),
     next_ev as (select * from events where status = 'upcoming' and event_date >= current_date order by event_date asc limit 1),
bouts as (
  select eb.event_id, eb.card, eb.bout_order, eb.weight_class, eb.is_title, eb.rounds, eb.winner, eb.method, eb.end_round, eb.end_time,
    json_build_object('id', eb.red_fighter_id, 'name', coalesce(rf.name, eb.red_name), 'ticker', rf.ticker, 'price', rf.price, 'rank', rf.rank,
      'champ', rf.is_champion, 'w', rf.ufc_wins, 'l', rf.ufc_losses, 'country', rf.country, 'division', rf.division, 'streak', rf.win_streak,
      'old', (select ph.old_price from price_history ph where ph.fighter_id = eb.red_fighter_id and ph.event_id = eb.event_id order by ph.changed_at asc limit 1),
      'new', (select ph.new_price from price_history ph where ph.fighter_id = eb.red_fighter_id and ph.event_id = eb.event_id order by ph.changed_at desc limit 1)) as red,
    json_build_object('id', eb.blue_fighter_id, 'name', coalesce(bf.name, eb.blue_name), 'ticker', bf.ticker, 'price', bf.price, 'rank', bf.rank,
      'champ', bf.is_champion, 'w', bf.ufc_wins, 'l', bf.ufc_losses, 'country', bf.country, 'division', bf.division, 'streak', bf.win_streak,
      'old', (select ph.old_price from price_history ph where ph.fighter_id = eb.blue_fighter_id and ph.event_id = eb.event_id order by ph.changed_at asc limit 1),
      'new', (select ph.new_price from price_history ph where ph.fighter_id = eb.blue_fighter_id and ph.event_id = eb.event_id order by ph.changed_at desc limit 1)) as blue
  from event_bouts eb
  left join fighters rf on rf.id = eb.red_fighter_id
  left join fighters bf on bf.id = eb.blue_fighter_id
  where eb.card = 'main'),
-- price 7 days ago = old_price of the first price change in the window (current price if no change)
risers as (
  select f.id, f.ticker, f.name, f.price,
         (select ph.old_price from price_history ph where ph.fighter_id = f.id and ph.changed_at >= now() - interval '7 days' order by ph.changed_at asc limit 1) as price_7d
  from fighters f where f.ticker is not null and coalesce(f.retired, false) = false),
top_risers as (
  select * from risers where price_7d > 0 and price >= 2 order by (price - price_7d) / price_7d desc limit 10),
admins as (select p.username from profiles p join user_roles ur on ur.user_id = p.id and ur.role = 'admin')
select json_build_object(
  'generated_at', now(),
  'last', (select json_build_object('id', e.id, 'name', e.name, 'date', e.event_date, 'venue', e.venue, 'location', e.location,
            'bouts', (select json_agg(b order by b.bout_order) from bouts b where b.event_id = e.id)) from last_ev e),
  'next', (select json_build_object('id', e.id, 'name', e.name, 'date', e.event_date, 'venue', e.venue, 'location', e.location,
            'bouts', (select json_agg(b order by b.bout_order) from bouts b where b.event_id = e.id)) from next_ev e),
  'risers_7d', (select json_agg(json_build_object('ticker', ticker, 'name', name, 'old', price_7d, 'new', price)) from top_risers),
  'profiles', (select json_object_agg(f.ticker, json_build_object(
      'name', f.name, 'ticker', f.ticker, 'price', f.price, 'prev_price', f.prev_price, 'fair_price', f.fair_price, 'country_code', f.country_code,
      'division', f.division, 'wins', f.wins, 'losses', f.losses, 'draws', f.draws,
      'ko_wins', f.ko_wins, 'sub_wins', f.sub_wins, 'dec_wins', f.dec_wins,
      'rank', f.rank, 'champ', f.is_champion, 'ufc_w', f.ufc_wins, 'ufc_l', f.ufc_losses, 'streak', f.win_streak,
      'flow_7d', (select json_build_object('buys', count(*) filter (where mf.kind = 'buy'), 'sells', count(*) filter (where mf.kind = 'sell'),
                          'shares_bought', coalesce(sum(abs(mf.shares)) filter (where mf.kind = 'buy'), 0),
                          'shares_sold', coalesce(sum(abs(mf.shares)) filter (where mf.kind = 'sell'), 0))
                  from market_flow mf where mf.fighter_id = f.id and mf.created_at >= now() - interval '7 days'),
      'last_fights', (select json_agg(x.e order by x.n) from jsonb_array_elements(coalesce(f.last_fights, '[]'::jsonb)) with ordinality as x(e, n) where x.n <= 5),
      'next_bout', (select json_build_object('event', e2.name, 'date', e2.event_date,
                      'opponent', case when eb2.red_fighter_id = f.id then eb2.blue_name else eb2.red_name end)
                    from event_bouts eb2 join events e2 on e2.id = eb2.event_id
                    where e2.status = 'upcoming' and e2.event_date >= current_date and (eb2.red_fighter_id = f.id or eb2.blue_fighter_id = f.id)
                    order by e2.event_date limit 1)))
    from fighters f
    where f.ticker is not null and (f.id in (
      select eb.red_fighter_id from event_bouts eb where eb.card = 'main' and eb.event_id in ((select id from last_ev), (select id from next_ev))
      union select eb.blue_fighter_id from event_bouts eb where eb.card = 'main' and eb.event_id in ((select id from last_ev), (select id from next_ev)))
      or f.id in (select id from top_risers))),
  'leaderboard', (select json_agg(t) from (select * from public.get_leaderboard('overall') g where g.username not in (select username from admins)) t),
  'leaderboard_monthly', (select json_agg(t) from (select * from public.get_leaderboard('monthly') g where g.username not in (select username from admins)) t)
) as d;
