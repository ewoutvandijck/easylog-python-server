import { z } from 'zod';

// Content type literals
const ContentType = z.enum([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp'
]);

// Text content schemas
export const textDeltaContentSchema = z.object({
  type: z.literal('text_delta'),
  content: z.string().describe('The text of the delta.')
});

export const textContentSchema = z.object({
  type: z.literal('text'),
  content: z.string().describe('The content of the message.')
});

// Tool-related schemas
export const toolUseContentSchema = z.object({
  type: z.literal('tool_use'),
  id: z.string().describe('The ID of the tool use.'),
  name: z.string().describe('The name of the tool.'),
  input: z.record(z.any()).describe('The arguments of the tool.')
});

export const toolResultContentSchema = z.object({
  type: z.literal('tool_result'),
  tool_use_id: z.string().describe('The ID of the tool use.'),
  content: z.string().describe('The result of the tool.'),
  content_format: z
    .enum(['image', 'chart', 'unknown'])
    .default('unknown')
    .describe('The format of the content.'),
  is_error: z
    .boolean()
    .default(false)
    .describe('Whether the tool result is an error.')
});

export const toolResultDeltaContentSchema = toolResultContentSchema.extend({
  type: z.literal('tool_result_delta')
});

// Media content schemas
export const imageContentSchema = z.object({
  type: z.literal('image'),
  content: z
    .string()
    .describe(
      'The raw base64 encoded image data, without any prefixes like `data:image/jpeg;base64,`'
    ),
  content_type: ContentType.default('image/jpeg').describe(
    'The content type of the image, must start with `image/`'
  )
});

export const pdfContentSchema = z.object({
  type: z.literal('pdf'),
  content: z
    .string()
    .describe(
      'The base64 encoded PDF data, without any prefixes like `data:application/pdf;base64,`'
    )
});

// Union type for all message content
export const messageContentSchema = z.discriminatedUnion('type', [
  textContentSchema,
  textDeltaContentSchema,
  toolUseContentSchema,
  toolResultContentSchema,
  toolResultDeltaContentSchema,
  imageContentSchema,
  pdfContentSchema
]);

// Type inference
export type MessageContent = z.infer<typeof messageContentSchema>;
