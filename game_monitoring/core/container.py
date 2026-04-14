"""
依赖注入容器实现

设计目标:
1. 轻量级、无外部依赖
2. 支持构造函数注入
3. 支持单例和瞬态生命周期
4. 类型安全的解析

使用示例:
```python
container = DIContainer()

# 注册类
container.register_class(Config, lifetime=LifetimeScope.SINGLETON)

# 注册接口到实现
container.register_interface(Logger, ConsoleLogger)

# 注册工厂
container.register_factory(Service, lambda c: Service(c.resolve(Config)))

# 解析
service = container.resolve(Service)  # 自动注入Config
```
"""

from typing import TypeVar, Type, Dict, Any, Callable, Optional, get_type_hints
from enum import Enum
import inspect
import threading

T = TypeVar('T')


class LifetimeScope(Enum):
    """服务生命周期作用域"""
    SINGLETON = "singleton"      # 全局单例
    TRANSIENT = "transient"      # 每次解析新实例
    SCOPED = "scoped"            # 作用域内单例


class ServiceDescriptor:
    """服务描述符 - 描述如何创建特定接口的实例"""

    def __init__(
        self,
        interface: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable] = None,
        instance: Optional[Any] = None,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ):
        self.interface = interface
        self.implementation = implementation
        self.factory = factory
        self.instance = instance  # 单例缓存
        self.lifetime = lifetime

    def __repr__(self):
        impl_name = self.implementation.__name__ if self.implementation else 'factory'
        return f"<ServiceDescriptor {self.interface.__name__} -> {impl_name}>"


class DIContainer:
    """
    轻量级依赖注入容器

    特性:
    - 自动构造函数注入: 通过类型注解自动解析依赖
    - 循环依赖检测: 避免无限递归
    - 多生命周期支持: 单例、瞬态、作用域
    - 线程安全: 使用锁保护共享状态
    """

    def __init__(self):
        self._registrations: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack: set = set()  # 检测循环依赖

    def register_class(
        self,
        cls: Type[T],
        *,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ) -> 'DIContainer':
        """注册类自身（自注册）"""
        descriptor = ServiceDescriptor(
            interface=cls,
            implementation=cls,
            lifetime=lifetime
        )
        self._registrations[cls] = descriptor
        return self

    def register_interface(
        self,
        interface: Type[T],
        implementation: Type[T],
        *,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ) -> 'DIContainer':
        """注册接口到实现的映射"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            lifetime=lifetime
        )
        self._registrations[interface] = descriptor
        return self

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[['DIContainer'], T],
        *,
        lifetime: LifetimeScope = LifetimeScope.TRANSIENT
    ) -> 'DIContainer':
        """注册工厂函数"""
        descriptor = ServiceDescriptor(
            interface=interface,
            factory=factory,
            lifetime=lifetime
        )
        self._registrations[interface] = descriptor
        return self

    def register_instance(self, interface: Type[T], instance: T) -> 'DIContainer':
        """注册已有实例（总是单例）"""
        descriptor = ServiceDescriptor(
            interface=interface,
            instance=instance,
            lifetime=LifetimeScope.SINGLETON
        )
        self._registrations[interface] = descriptor
        self._singletons[interface] = instance
        return self

    def resolve(self, interface: Type[T]) -> T:
        """
        解析依赖

        Args:
            interface: 要解析的接口/类

        Returns:
            接口的实现实例

        Raises:
            KeyError: 未注册的依赖
            CircularDependencyError: 检测到循环依赖
        """
        # 检查循环依赖
        if interface in self._resolution_stack:
            raise CircularDependencyError(
                f"检测到循环依赖: {' -> '.join(self._resolution_stack)} -> {interface}"
            )

        with self._lock:
            # 检查是否是单例
            if interface in self._singletons:
                return self._singletons[interface]

            descriptor = self._registrations.get(interface)
            if not descriptor:
                raise KeyError(f"未注册的依赖: {interface.__name__}")

            # 创建实例
            self._resolution_stack.add(interface)
            try:
                instance = self._create_from_descriptor(descriptor)
            finally:
                self._resolution_stack.discard(interface)

            # 缓存单例
            if descriptor.lifetime == LifetimeScope.SINGLETON:
                self._singletons[interface] = instance

            return instance

    def _create_from_descriptor(self, descriptor: ServiceDescriptor) -> Any:
        """根据描述符创建实例"""
        if descriptor.instance:
            return descriptor.instance

        if descriptor.factory:
            return descriptor.factory(self)

        if descriptor.implementation:
            return self._create_with_injection(descriptor.implementation)

        raise ValueError(f"无法创建 {descriptor.interface} 的实例")

    def _create_with_injection(self, cls: Type[T]) -> T:
        """
        自动解析构造函数参数并创建实例

        使用inspect检测构造函数签名，自动注入依赖
        """
        try:
            init_method = getattr(cls, '__init__', None)
            if init_method is None:
                return cls()

            # 获取参数类型提示
            type_hints = get_type_hints(init_method)
            sig = inspect.signature(init_method)
            parameters = list(sig.parameters.items())

            # 跳过'self'
            if parameters:
                parameters = parameters[1:]

            # 准备构造函数参数
            args = []
            kwargs = {}

            for param_name, param in parameters:
                param_type = type_hints.get(param_name)

                # 如果有默认值且没有类型提示，跳过
                if param.default is not inspect.Parameter.empty and param_type is None:
                    continue

                # 尝试解析依赖
                if param_type:
                    try:
                        # 处理Optional[T]
                        origin = getattr(param_type, '__origin__', None)
                        if origin is not None:
                            args_types = getattr(param_type, '__args__', None)
                            if args_types and type(None) in args_types:
                                # Optional[X]，取X
                                param_type = next(t for t in args_types if t is not type(None))

                        resolved = self.resolve(param_type)

                        if param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                            args.append(resolved)
                        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
                            kwargs[param_name] = resolved

                    except KeyError:
                        # 未注册但可选
                        if param.default is not inspect.Parameter.empty:
                            continue
                        if isinstance(param_type, type) and param_type.__name__ == 'NoneType':
                            args.append(None)
                        else:
                            raise

            return cls(*args, **kwargs)

        except Exception as e:
            raise RuntimeError(f"创建 {cls.__name__} 实例失败: {e}") from e

    def create_scope(self) -> 'DIScope':
        """创建新的作用域"""
        return DIScope(self)

    def is_registered(self, interface: Type) -> bool:
        """检查是否已注册"""
        return interface in self._registrations

    def list_registrations(self) -> Dict[Type, ServiceDescriptor]:
        """列出所有注册（用于调试）"""
        return dict(self._registrations)


class DIScope:
    """
    依赖注入作用域

    用于管理SCOPED生命周期的实例
    """

    def __init__(self, container: DIContainer):
        self._container = container
        self._scoped_instances: Dict[Type, Any] = {}

    def resolve(self, interface: Type[T]) -> T:
        """在作用域内解析"""
        descriptor = self._container._registrations.get(interface)
        if descriptor and descriptor.lifetime == LifetimeScope.SCOPED:
            if interface in self._scoped_instances:
                return self._scoped_instances[interface]

            instance = self._container.resolve(interface)
            self._scoped_instances[interface] = instance
            return instance

        return self._container.resolve(interface)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._scoped_instances.clear()


class CircularDependencyError(Exception):
    """循环依赖错误"""
    pass
