import { Message } from '@/app/schemas/messages';
import { atom } from 'jotai';

export const loadingAtom = atom<boolean>(false);
export const userMessageAtom = atom<Message | null>(null);
export const assistantMessageAtom = atom<Message | null>(null);
