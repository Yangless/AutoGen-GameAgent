"""
DI容器单元测试
"""

import pytest
from game_monitoring.core.container import DIContainer, LifetimeScope, CircularDependencyError


class TestDIContainer:
    """DI容器测试"""

    def test_register_and_resolve_class(self):
        """测试类注册和解析"""
        class ServiceA:
            pass

        container = DIContainer()
        container.register_class(ServiceA, lifetime=LifetimeScope.SINGLETON)

        service = container.resolve(ServiceA)
        assert isinstance(service, ServiceA)

    def test_singleton_returns_same_instance(self):
        """测试单例返回相同实例"""
        class Database:
            pass

        container = DIContainer()
        container.register_class(Database, lifetime=LifetimeScope.SINGLETON)

        db1 = container.resolve(Database)
        db2 = container.resolve(Database)

        assert db1 is db2

    def test_transient_returns_different_instance(self):
        """测试瞬态返回不同实例"""
        class Service:
            pass

        container = DIContainer()
        container.register_class(Service, lifetime=LifetimeScope.TRANSIENT)

        s1 = container.resolve(Service)
        s2 = container.resolve(Service)

        assert s1 is not s2

    def test_factory_registration(self):
        """测试工厂函数注册"""
        class Config:
            def __init__(self, value):
                self.value = value

        container = DIContainer()
        container.register_factory(
            Config,
            lambda c: Config(value="test"),
            lifetime=LifetimeScope.SINGLETON
        )

        config = container.resolve(Config)
        assert config.value == "test"

    def test_constructor_injection(self):
        """测试构造函数自动注入"""
        class Logger:
            pass

        class Service:
            def __init__(self, logger: Logger):
                self.logger = logger

        container = DIContainer()
        container.register_class(Logger)
        container.register_class(Service)

        service = container.resolve(Service)
        assert isinstance(service.logger, Logger)

    def test_instance_registration(self):
        """测试实例注册"""
        class Config:
            pass

        config = Config()
        container = DIContainer()
        container.register_instance(Config, config)

        resolved = container.resolve(Config)
        assert resolved is config

    def test_interface_to_implementation(self):
        """测试接口到实现映射"""
        class Interface:
            pass

        class Implementation(Interface):
            pass

        container = DIContainer()
        container.register_interface(Interface, Implementation)

        impl = container.resolve(Interface)
        assert isinstance(impl, Implementation)

    def test_unregistered_dependency_raises(self):
        """测试未注册依赖报错"""
        class Unknown:
            pass

        container = DIContainer()

        with pytest.raises(KeyError):
            container.resolve(Unknown)
