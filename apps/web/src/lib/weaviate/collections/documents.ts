import { dataType, vectorizer } from 'weaviate-client';

import getWeaviateClient from '../client';

const getDocumentsCollection = async (forceRecreate = false) => {
  const client = await getWeaviateClient();

  const exists = await client.collections.exists('Document');

  if (!exists || forceRecreate) {
    if (exists) {
      await client.collections.delete('Document');
    }

    await client.collections.create({
      name: 'Document',
      vectorizers: vectorizer.text2VecOpenAI(),
      properties: [
        { name: 'filename', dataType: dataType.TEXT },
        { name: 'organizationId', dataType: dataType.UUID },
        { name: 'summary', dataType: dataType.TEXT },
        { name: 'tags', dataType: dataType.TEXT_ARRAY }
      ]
    });
  }

  return client.collections.get<{
    filename: string;
    organizationId: string;
    summary: string;
    tags: string[];
  }>('Document');
};

export default getDocumentsCollection;
