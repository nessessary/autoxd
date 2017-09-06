------------------------------------------------
-- 2017/8/26 for sqlite
-- 沪深历史数据


-- 记录股票分时数据
drop table if exists fenshi;
create table fenshi (
id  INT PRIMARY KEY     NOT NULL,
stock_code char(7) not null,			--股票代码, 有blob字段后必须加索引
fenshi_day date not null,							--分时日期
fenshi_data blob not null							--分时数据
);
create index idt_stock_code on fenshi(stock_code);

--日k线数据
drop table if exists kline;
create table kline (
id  INT PRIMARY KEY     NOT NULL,
stock_code char(7) not null,				--股票代码
kline_time date not null,					--k线日期
kline_open float,							--开盘价
kline_high float,							--最高价
kline_low float,							--最低价
kline_close float,							--收盘价
kline_volume float,							--成交量
kline_amount float							--成交金额
);
create index idt1_stock_code on kline(stock_code);
create index idt2_kline_time on kline(kline_time);

--5分钟k线数据
drop table if exists kline5min;
create table kline5min (
id  INT PRIMARY KEY     NOT NULL,
stock_code char(7) not null,				--股票代码
kline_time date not null,					--k线日期
kline_open float,							--开盘价
kline_high float,							--最高价
kline_low float,							--最低价
kline_close float,							--收盘价
kline_volume float							--成交量
);
create index idt3_stock_code on kline5min(stock_code);
create index idt4_kline_time on kline5min(kline_time);