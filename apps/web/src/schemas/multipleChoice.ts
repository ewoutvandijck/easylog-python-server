import { z } from 'zod';

/** Schema for a choice in a multiple-choice question */
export const choiceSchema = z.object({
  label: z.string().describe('The (text) label of the choice'),
  value: z.string().describe('The value of the choice')
});

export type Choice = z.infer<typeof choiceSchema>;

/** Schema for a multiple-choice widget */
export const multipleChoiceSchema = z.object({
  type: z.literal('multiple_choice').default('multiple_choice'),
  question: z.string().describe('The question text presented to the user'),
  choices: z.array(choiceSchema),
  selected_choice: z.string().nullable().optional()
});

export type MultipleChoiceWidget = z.infer<typeof multipleChoiceSchema>;
