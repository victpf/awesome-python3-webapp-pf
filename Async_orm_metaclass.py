import aiomysql
import asyncio
global tasks_list
#协程
async def create_pool(loop, **kw):
    #logging.info('create database connection pool...')
    print('create database connection pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

#协程
async def select(sql, args, size=None):
    global __pool
    print('sql: %s'%sql)
    print('args: %s'%args)
    print('size: %d'%size)
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?','%s'), args or ())
        if size:
            rs = await cur.fetchall(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs

#协程
async def execute(sql, args):
    #log(sql)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected

def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)

class Field(object):

    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s, %s>' %(self.__class__.__name__,self.column_type, self.name)

class StringField(Field):

    def __init__(self, name=None, column_type = 'varchar(100)', primary_key = False, default = None):
        super(StringField, self).__init__(name, column_type, primary_key, default)

class IntegerField(Field):

    def __init__(self, name=None, column_type = 'bigint', primary_key = False, default = None):
        super(IntegerField, self).__init__(name, column_type, primary_key, default)

class TextField(Field):

    def __init__(self, name=None, column_type = 'longtext', primary_key = False, default = None):
        super(IntegerField, self).__init__(name, column_type, primary_key, default)
class BooleanField(Field):

    def __init__(self, name=None, column_type = 'bool', primary_key = False, default = None):
        super(IntegerField, self).__init__(name, column_type, primary_key, default)

class FloatField(Field):

    def __init__(self, name=None, column_type = 'real', primary_key = False, default = None):
        super(IntegerField, self).__init__(name, column_type, primary_key, default)
class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        tableName = attrs.get('__table__', None) or name
        print('found model: %s(table:%s)' % (name, tableName))
        #获取所有Field和主键名
        mappings = dict()
        fields = []
        primaryKey = None
        for k,v in attrs.items():
          print('k: %s                --- v: %s '%(k,v))  
          if isinstance(v,Field):
                print('founding mapping:%s ==> %s'%(k,v))
                mappings[k] = v
                if v.primary_key:
                    #找到主键
                    print('primaryKey : %s'%primaryKey)
                    if primaryKey:
                        #主键不能重复
                        raise RuntimeError('Duplicate primary key for field:%s' %k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('primaryKey not found')
        for k in mappings.keys():
            attrs.pop(k)
#给列表里边每个元素加上单引号，然后重新保存在列表中  
        escaped_fields = list(map(lambda f:'%s' %f, fields))
        print('fields  :',fields)
        print('escaped_fields: ',escaped_fields)
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey #主属性名
        attrs['__fields__'] = fields #除主键外的属性名
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)

class Model(dict, metaclass = ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s:%s'%(key, str(value)))
                setattr(self, key, value)
        return value

    #协程
    async def find(cls, pk):
        'find object by primaryKey'
        print('cls: %s'%cls)
        rs = await select('%s where %s = ?' % (cls.__select__, cls.__primary_key__), [pk], 1)
#        rs = await select('%s where %s = ?' % (cls.__select__, cls.__primary_key__), [pk])
        print('rs: %s'%rs)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    #协程
    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        print('args: %s'%args)
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        print(rows)
        if rows != 1:
            logging.warn('failed to insert record:affected rows:%s'%rows)

class User(Model):
    __table__ = 'users'

    id = IntegerField(primary_key = True)
    name = StringField()

#协程
async def destory_pool():
    global __pool
    if __pool is not None:
        __pool.close()
        await __pool.wait_closed()

#协程    
async def test():
    await create_pool(loop,user = 'root',password = 'songj883',db = 'test',host = '127.0.0.1')
    u = User(id=233, name='pf')
#    await u.find('123')
    await output(u)
    await u.save()
    await destory_pool()
async def output(c):
    print('__mappings__       : %s '%c.__mappings__)
    print('__table__          : %s '%c.__table__)
    print('__primary_key__    : %s '%c.__primary_key__)
    print('__fields__         : %s '%c.__fields__)
    print('__select__          : %s '%c.__select__)
    print('__insert__          : %s '%c.__insert__)
    print('__delete__          : %s '%c.__delete__)
    print('__update__          : %s '%c.__update__)
'''
def tasks():
    global tasks_list 
    tasks_list=[]
    for i in range(1):
        tasks_list.append(test(id=i,name=str(('pf+%d')%i)))
    return tasks_list
if __name__=='__main__':
    tasks()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks_list))
    loop.close()
'''
loop = asyncio.get_event_loop()
tasks=[test()]
loop.run_until_complete(asyncio.wait(tasks))
loop.close()

