-- удаляє таблицю
-- drop table if exists entries;

-- створює пусту таблицю
-- створити таблицю для продукції
create table if not exists `products`
(
   id integer primary key autoincrement,
   name text not null ,
   model text not null ,
   price text not null ,
   quantity integer
);

-- створити таблицю для реєстрації
create table  if not exists `users`
(
    id integer primary key autoincrement ,
    is_admin integer  not  null,
    login_ text  not null,
    password text  not null,
    name text not null,
    surname text not null,
    tel text not null,
    email text not  null
);
-- створити таблицю для кошика
create table if not exists `basket`
(
   id integer not null primary key autoincrement,
   productsId integer not null ,
   quantity integer not null,
   userId integer not null

);


create index if not exists `id` on `basket` (
  `id`
);

--створити таблицю для продукції від дистрибюторів
create table if not exists  `distributors`
(
  id integer primary key autoincrement,
  name text not null,
  model text not null ,
  price text not null ,
  quantity integer,
  sum text not null ,
  company text not null ,
  date text not null
);

--створити таблицю для покупців

create table if not exists `customers`
(
  id integer primary key autoincrement ,
  name text not null ,
  model text not null ,
  price text not null ,
  quantity text not null ,
  customer text not null ,
  date text not null
);

--створити таблицю історію попкупок для покупців

create table if not exists `history`
(
  id integer primary key autoincrement ,
  product_id text not null ,
  quantity text not null ,
  price text not null ,
  date text not null,
  id_user text not null,
  id_card text not null
);

--створити таблицю card
create table  if not exists `cards`
( id integer primary key autoincrement ,
number text not null ,
valid text not null ,
svv text not null,
id_user text not null,
id_card text not null

);