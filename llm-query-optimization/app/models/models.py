from sqlalchemy import Column, Integer, String, ForeignKey
from app.db import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    invoice_number = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    invoice_number = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    customer_name = Column(String, nullable=False)
    content = Column(String, nullable=False)