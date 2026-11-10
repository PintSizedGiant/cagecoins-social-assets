-- Cage Coins social: one read-only query that returns everything build.py needs.
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
  where eb.card = 'main')
select json_build_object(
  'generated_at', now(),
  'last', (select json_build_object('id', e.id, 'name', e.name, 'date', e.event_date, 'venue', e.venue, 'location', e.location,
            'bouts', (select json_agg(b order by b.bout_order) from bouts b where b.event_id = e.id)) from last_ev e),
  'next', (select json_build_object('id', e.id, 'name', e.name, 'date', e.event_date, 'venue', e.venue, 'location', e.location,
            'bouts', (select json_agg(b order by b.bout_order) from bouts b where b.event_id = e.id)) from next_ev e),
  'traders', (select json_agg(t) from (
      select p.username, p.month_start, p.month_start_value,
             p.balance + coalesce((select sum(po.shares * f.price) from positions po join fighters f on f.id = po.fighter_id where po.user_id = p.id), 0) as net_worth
      from profiles p where not exists (select 1 from user_roles ur where ur.user_id = p.id and ur.role = 'admin')) t)
) as d;
