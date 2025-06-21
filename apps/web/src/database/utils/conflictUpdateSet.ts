import { Column, sql } from 'drizzle-orm';
import { PgTable, PgUpdateSetSource } from 'drizzle-orm/pg-core';

/**
 * Helper function to generate the SET clause for ON CONFLICT DO UPDATE
 * statements in Drizzle ORM. Takes a table and list of columns and returns an
 * object mapping those columns to their EXCLUDED values.
 *
 * @example
 *   ```ts
 *   await db.insert(users)
 *     .values(newUser)
 *     .onConflictDoUpdate({
 *       target: users.email,
 *       set: conflictUpdateSet(users, ['name', 'updatedAt'])
 *     });
 *   ```;
 *
 * @param table - The Drizzle table object to generate the SET clause for
 * @param columns - Array of column names to include in the SET clause
 * @returns Object mapping column names to their EXCLUDED values for use in
 *   onConflictDoUpdate
 */
function conflictUpdateSet<TTable extends PgTable>(
  table: TTable,
  columns: (keyof TTable['_']['columns'] & keyof TTable)[]
): PgUpdateSetSource<TTable> {
  return Object.assign(
    {},
    ...columns.map((k) => ({
      [k]: sql.raw(`excluded.${(table[k] as Column).name}`)
    }))
  ) as PgUpdateSetSource<TTable>;
}

export default conflictUpdateSet;
