"""Free-feed and Apify aggregator sources.

Every module here exposes ``fetch_jobs(http) -> list[Job]``, same shape as
the Romanian aggregators (hipo/ejobs/bestjobs/...). They are registered in
``internscout.sources.feeds.registry.FEEDS``.
"""
