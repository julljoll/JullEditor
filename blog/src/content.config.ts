import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Esquema ESPEJO del contrato Python (backend/astro_publisher.py).
 * Si este esquema y validate_frontmatter() divergen, el test de
 * contrato de tests/test_astro_publisher.py lo detecta.
 */
const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string().min(1).max(200),
    description: z.string().min(1).max(170),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: z.string().min(1),
    slug: z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/),
    tags: z.array(z.string()).min(1).max(6),
    category: z.string().default('science_tech'),
    heroImage: z.string().optional(),
    seoKeyword: z.string().optional(),
    readingTime: z.number().int().positive().default(1),
    featured: z.boolean().default(false),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
