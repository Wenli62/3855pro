from sqlalchemy import Integer, Numeric, String, DateTime, func, BigInteger
from sqlalchemy.orm import DeclarativeBase, mapped_column
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass

class onlineOrderReport(Base):
    # SQLALchemy column definitions
    __tablename__ = 'online_orders'
    id = mapped_column(Integer, primary_key=True)
    cid = mapped_column(String(10), nullable=False)
    order_amount = mapped_column(Numeric(10, 2), nullable=False)
    shipping_address = mapped_column(String(100), nullable=False)
    order_time = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(BigInteger, nullable=False)

    def to_dict(self):
        dict = {}
        dict['id'] = self.id
        dict['cid'] = self.cid
        dict['order_amount']= float(self.order_amount)
        dict['shipping_address']= self.shipping_address
        dict['order_time']= self.order_time
        dict['date_created']= self.date_created
        dict['trace_id'] = self.trace_id

        return dict

class storeSalesReport(Base):
    __tablename__ = 'store_sales'
    id = mapped_column(Integer, primary_key=True)
    sid = mapped_column(String(10), nullable=False)
    sale_amount = mapped_column(Numeric(10, 2), nullable=False)
    payment_method = mapped_column(String(15), nullable=False)
    sale_time = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    trace_id = mapped_column(BigInteger, nullable=False)

    def to_dict(self):
        dict = {}
        dict['id'] = self.id
        dict['sid'] = self.sid
        dict['sale_amount']= float(self.sale_amount)
        dict['payment_method']= self.payment_method
        dict['sale_time']= self.sale_time
        dict['date_created']= self.date_created
        dict['trace_id'] = self.trace_id

        return dict