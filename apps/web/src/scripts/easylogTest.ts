import easylogDb from '@/lib/easylog/db';

const test = async () => {
  const result = await easylogDb.execute('SELECT * FROM users');
  console.log(result);
};

void test();
