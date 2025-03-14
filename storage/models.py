from sqlalchemy import Integer, Numeric, String, DateTime, func
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

    #If you want the timestamp to be consistent and always generated by the database, 
    #you could use func.now() in SQLAlchemy instead of generating the timestamp in Python.
    #This will ensure that the timestamp is generated on the database side when the record is inserted

    #If you generate datetime.now(timezone.utc) once, 
    #say for an insert into a database, the same timestamp value will be used for all rows inserted during that time,
    #even if multiple inserts occur quickly. The time won’t change until the Python code makes another call to datetime.now(timezone.utc) that reflects a time change.
    
    #date_created = mapped_column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

    trace_id = mapped_column(Numeric(20,0), nullable=False)

# constructor not needed
    # def __init__(self, cid, order_amount, shipping_address, order_time, date_created=None):
    #     self.cid = cid
    #     self.order_amount = order_amount
    #     self.shipping_address = shipping_address
    #     self.order_time = order_time
    #     # self.date_created = date_created or datetime.now()

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
    trace_id = mapped_column(Numeric(20,0), nullable=False)

    # def __init__(self, sid, sale_amount, payment_method, sale_time, date_created=None):
    #     self.sid = sid
    #     self.sale_amount = sale_amount
    #     self.payment_method = payment_method
    #     self.sale_time = sale_time
    #     self.date_created = date_created or datetime.now()

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