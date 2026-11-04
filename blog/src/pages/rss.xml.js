import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import config from 'astro/config';

export async function GET(context) {
  const articles = (await getCollection('blog', ({ data }) => !data.draft)).sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf(),
  );
  return rss({
    title: 'Pericial Blog',
    description: 'Artículos periciales, tecnología y derecho digital.',
    site: context.site ?? config.site,
    items: articles.map((a) => ({
      title: a.data.title,
      description: a.data.description,
      pubDate: a.data.pubDate,
      link: `/${a.data.slug}`,
      categories: a.data.tags,
    })),
    customData: '<language>es</language>',
  });
}
