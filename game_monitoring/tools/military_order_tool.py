import json
from typing import Dict, Any, List
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from config import doubao_client, qwen_client
import traceback

def generate_batch_military_orders(commander_order: str = None) -> str:
    """
    批量生成多个玩家的个性化军令
    
    Args:
        commander_order: 指挥官总军令（可选，如果不提供则使用默认）
    
    Returns:
        批量生成结果的JSON字符串
    """
    from ..context import get_players_info, get_commander_order
    
    # 获取指挥官总军令
    if commander_order is None:
        commander_order = get_commander_order()
    
    # 获取所有玩家信息
    players_info = get_players_info()
    
    batch_results = []
    
    for player_name, player_info in players_info.items():
        try:
            # 为每个玩家生成个性化军令
            result = generate_military_order_with_llm(
                player_name=player_info["player_name"],
                player_id=player_name.lower().replace(" ", "_"),
                team_stamina=player_info["team_stamina"],
                backpack_items=player_info["backpack_items"],
                team_levels=player_info["team_levels"],
                skill_levels=player_info["skill_levels"],
                reserve_troops=player_info["reserve_troops"],
                commander_order=commander_order
            )
            
            result_data = json.loads(result)
            batch_results.append({
                "player_name": player_name,
                "status": "success",
                "military_order": result_data["military_order"],
                "team_analysis": result_data["team_analysis"]
            })
            
        except Exception as e:
            batch_results.append({
                "player_name": player_name,
                "status": "error",
                "error": str(e)
            })
    
    final_result = {
        "status": "completed",
        "total_players": len(players_info),
        "successful_orders": len([r for r in batch_results if r["status"] == "success"]),
        "failed_orders": len([r for r in batch_results if r["status"] == "error"]),
        "commander_order": commander_order,
        "generated_at": datetime.now().isoformat(),
        "results": batch_results
    }
    
    print(f"--- 批量军令生成完成 ---")
    print(f"  - 总玩家数: {final_result['total_players']}")
    print(f"  - 成功生成: {final_result['successful_orders']}")
    print(f"  - 生成失败: {final_result['failed_orders']}")
    
    return json.dumps(final_result, ensure_ascii=False, indent=2)

def generate_personalized_military_order(
    player_id: str,
    player_name: str,
    team_stamina: list,
    backpack_items: list,
    team_levels: list,
    skill_levels: list,
    reserve_troops: int,
    event_info: Dict[str, Any] = None,
    commander_order: str = None
) -> str:
    """
    生成个性化军令内容（兼容性函数）
    
    这个函数保持原有的接口，内部调用新的工具函数
    
    Args:
        player_id: 玩家ID
        player_name: 玩家姓名
        team_stamina: 队伍体力列表
        backpack_items: 背包道具列表
        team_levels: 队伍等级列表
        skill_levels: 技能等级列表
        reserve_troops: 预备兵数量
        event_info: 事件信息（可选）
        commander_order: 指挥官总军令（可选）
    
    Returns:
        个性化军令内容的JSON字符串
    """
    # 直接调用新的工具函数
    return generate_military_order_with_llm(
        player_name=player_name,
        player_id=player_id,
        team_stamina=team_stamina,
        backpack_items=backpack_items,
        team_levels=team_levels,
        skill_levels=skill_levels,
        reserve_troops=reserve_troops,
        event_info=event_info,
        commander_order=commander_order
    )

def get_team_assignment(level: int, team_number: int) -> str:
    """根据队伍等级获取任务分配"""
    if level >= 50:
        return f"第{team_number}队主力需要能打12级地，直接前往前线(752, 613)，注意兵种克制"
    elif level >= 45:
        return f"第{team_number}队需要能打11级地，可酌情考虑派往前线或集结待命"
    elif level >= 40:
        return f"第{team_number}队需要能打8级地，派遣至将军雕像(732, 767)集结"
    elif level >= 35:
        return f"第{team_number}队需要能打6级地，作为攻城拆迁队使用"
    else:
        return f"第{team_number}队建议继续提升等级，暂时待命"

def create_llm_content_generator() -> AssistantAgent:
    """创建纯粹的LLM内容生成引擎"""
    return AssistantAgent(
        name="MilitaryOrderContentGenerator",
        system_message=(
            "你是一名资深的军事策略专家和军令撰写大师。你的任务是根据指挥官总军令和玩家的具体情况，"
            "为每个玩家生成个性化的作战军令。\n\n"
            "**你的角色定位：**\n"
            "- 你是游戏中的军事顾问，负责将总体战略转化为具体的个人作战指令\n"
            "- 你需要根据玩家的队伍实力、装备情况和资源状况，制定最适合的作战方案\n"
            "- 你的军令应该既体现总体战略意图，又充分考虑玩家的个人能力\n\n"
            "**军令生成要求：**\n"
            "1. 军令格式要正式、有仪式感，体现军事文书的严肃性\n"
            "2. 内容要具体明确，包含具体的坐标、时间、任务分工\n"
            "3. 要根据玩家队伍等级合理分配任务（50级以上主攻，45级以上支援，40级以上拆迁）\n"
            "4. 要提及玩家的资源情况（预备兵、道具等）并给出使用建议\n"
            "5. 语言要有激励性和荣誉感，激发玩家的参战热情\n"
            "6. 军令长度控制在300-500字之间\n\n"
            "**输出格式：**\n"
            "请直接输出完整的军令内容，不需要额外的解释或格式标记。"
        ),
        description="专门生成个性化军令内容的LLM引擎",
        model_client=doubao_client,
        tools=[],
        reflect_on_tool_use=False,
    )

def generate_military_order_with_llm(
    player_name: str,
    player_id: str = None,
    team_stamina: list = None,
    backpack_items: list = None,
    team_levels: list = None,
    skill_levels: list = None,
    reserve_troops: int = 0,
    event_info: Dict[str, Any] = None,
    commander_order: str = None
) -> str:
    """
    工具函数：使用LLM生成个性化军令内容
    
    这是一个Agent可以调用的工具函数，负责调用LLM生成军令内容。
    
    Args:
        player_name: 玩家姓名
        player_id: 玩家ID（可选）
        team_stamina: 队伍体力列表（可选）
        backpack_items: 背包道具列表（可选）
        team_levels: 队伍等级列表（可选）
        skill_levels: 技能等级列表（可选）
        reserve_troops: 预备兵数量（可选）
        event_info: 事件信息（可选）
        commander_order: 指挥官总军令（可选）
    
    Returns:
        生成的军令内容JSON字符串
    """
    from ..context import get_commander_order
    
    # 获取指挥官总军令
    if commander_order is None:
        commander_order = get_commander_order()
    
    # 设置默认值
    if team_stamina is None:
        team_stamina = [100, 90, 80, 70]
    if backpack_items is None:
        backpack_items = []
    if team_levels is None:
        team_levels = [45, 40, 35, 30]
    if skill_levels is None:
        skill_levels = [20, 18, 15, 12]
    if event_info is None:
        event_info = {
            "event_date": "9月15号",
            "event_time": "早上10点",
            "event_type": "攻城战",
            "target_coordinates": "(752, 613)",
            "rally_point": "(732, 767)",
            "max_recruitment": 30000
        }
    
    # 分析玩家能力
    team_assignments = []
    for i, (level, stamina) in enumerate(zip(team_levels[:4], team_stamina[:4])):
        if level > 0 and stamina > 50:
            capability = get_team_capability(level)
            team_assignments.append({
                "team_number": i + 1,
                "level": level,
                "stamina": stamina,
                "capability": capability,
                "assignment": get_team_assignment(level, i + 1)
            })
    
    # 调用LLM生成军令内容
    military_order_content = _call_llm_for_content_generation(
        player_name, team_assignments, backpack_items, reserve_troops, event_info, commander_order
    )
    
    # 构建返回结果
    result = {
        "status": "success",
        "player_id": player_id or player_name.lower().replace(" ", "_"),
        "player_name": player_name,
        "military_order": military_order_content,
        "commander_order": commander_order,
        "generated_at": datetime.now().isoformat(),
        "team_analysis": team_assignments
    }
    
    print(f"--- 工具：军令生成完成 ---")
    print(f"  - 玩家: {player_name}")
    print(f"  - 军令长度: {len(military_order_content)}字符")
    
    return json.dumps(result, ensure_ascii=False, indent=2)

def get_team_capability(level: int) -> str:
    """根据队伍等级判断能力"""
    if level >= 50:
        return "12级地"
    elif level >= 45:
        return "11级地"
    elif level >= 40:
        return "8级地"
    elif level >= 35:
        return "6级地"
    else:
        return "4级地"

def _call_llm_for_content_generation(
    player_name: str, 
    team_assignments: list, 
    backpack_items: list, 
    reserve_troops: int, 
    event_info: Dict[str, Any],
    commander_order: str = None
) -> str:
    """内部函数：调用LLM生成军令内容"""
    
    # 创建LLM内容生成引擎
    llm_generator = create_llm_content_generator()
    
    # 构建玩家数据的自然语言描述
    player_data_desc = build_player_data_description(
        player_name, team_assignments, backpack_items, reserve_troops, event_info
    )
    
    # 构建完整的提示词
    if commander_order:
        prompt = f"""请根据以下信息为玩家生成个性化军令：

**指挥官总军令：**
{commander_order}

**玩家具体情况：**
{player_data_desc}

请生成一份既符合总军令战略意图，又适合该玩家具体情况的个性化作战军令。"""
    else:
        prompt = f"""请根据以下玩家情况生成个性化军令：

**玩家具体情况：**
{player_data_desc}

**默认作战目标：**
- 事件：{event_info.get('event_type', '攻城战')}
- 时间：{event_info.get('event_time', '早上10点')}
- 目标坐标：{event_info.get('target_coordinates', '(752, 613)')}
- 集结点：{event_info.get('rally_point', '(732, 767)')}

请生成一份适合该玩家的个性化作战军令。"""
    
    # 直接调用LLM生成军令
    try:
        import asyncio
        
        # 创建用户消息
        user_message = TextMessage(content=prompt, source="user")
        
        # 异步调用LLM生成回复
        async def call_llm():
            response = await llm_generator.on_messages([user_message], cancellation_token=None)
            return response
        
        # 运行异步调用
        response = asyncio.run(call_llm())
        
        # 提取生成的军令内容
        if response and response.chat_message:
            military_order = response.chat_message.content
            print(f"--- LLM生成军令成功 ---")
            print(f"  - 玩家: {player_name}")
            print(f"  - 军令内容: {military_order}")
            print(f"  - 军令长度: {len(military_order)}字符")
            return military_order
        else:
            print(f"--- LLM生成军令失败，使用备用方案 ---")
            return generate_fallback_military_order(player_name, team_assignments, backpack_items, reserve_troops, event_info)
            
    except Exception as e:
        print(f"--- LLM调用异常: {str(e)}，使用备用方案 ---")
        traceback.print_exc()
        return generate_fallback_military_order(player_name, team_assignments, backpack_items, reserve_troops, event_info)

def build_player_data_description(
    player_name: str,
    team_assignments: list,
    backpack_items: list,
    reserve_troops: int,
    event_info: Dict[str, Any]
) -> str:
    """将玩家数据转换为自然语言描述"""
    
    desc_parts = []
    
    # 玩家基本信息
    desc_parts.append(f"**玩家姓名：** {player_name}")
    
    # 队伍情况分析
    if team_assignments:
        desc_parts.append("\n**队伍战力分析：**")
        for assignment in team_assignments:
            level = assignment['level']
            stamina = assignment['stamina']
            team_num = assignment['team_number']
            capability = assignment['capability']
            
            if level >= 50:
                role = "主力攻坚部队"
            elif level >= 45:
                role = "精锐支援部队"
            elif level >= 40:
                role = "攻城拆迁部队"
            else:
                role = "后备部队"
                
            desc_parts.append(f"- 第{team_num}队：{level}级，体力{stamina}%，可打{capability}，适合作为{role}")
    else:
        desc_parts.append("\n**队伍战力分析：** 暂无可用队伍")
    
    # 资源情况
    desc_parts.append(f"\n**资源状况：**")
    desc_parts.append(f"- 预备兵数量：{reserve_troops}")
    
    if backpack_items:
        items_text = "、".join(backpack_items[:5])  # 显示前5个道具
        desc_parts.append(f"- 携带道具：{items_text}")
    else:
        desc_parts.append(f"- 携带道具：无")
    
    # 作战环境
    desc_parts.append(f"\n**作战环境：**")
    desc_parts.append(f"- 作战时间：{event_info.get('event_date', '9月15号')} {event_info.get('event_time', '早上10点')}")
    desc_parts.append(f"- 作战类型：{event_info.get('event_type', '攻城战')}")
    desc_parts.append(f"- 目标坐标：{event_info.get('target_coordinates', '(752, 613)')}")
    desc_parts.append(f"- 集结地点：{event_info.get('rally_point', '(732, 767)')}")
    desc_parts.append(f"- 可募兵上限：{event_info.get('max_recruitment', 30000)}")
    
    return "\n".join(desc_parts)

def generate_fallback_military_order(
    player_name: str,
    team_assignments: list,
    backpack_items: list,
    reserve_troops: int,
    event_info: Dict[str, Any]
) -> str:
    """备用军令生成方案（简化版硬编码）"""
    
    main_team = team_assignments[0] if team_assignments else None
    main_level = main_team['level'] if main_team else 0
    
    if main_level >= 50:
        role = "主力先锋"
        task = f"直接前往前线{event_info.get('target_coordinates', '(752, 613)')}，清除城内守军"
    elif main_level >= 45:
        role = "精锐支援"
        task = f"前往集结点{event_info.get('rally_point', '(732, 767)')}，作为第二梯队支援主力"
    else:
        role = "攻城部队"
        task = f"前往集结点{event_info.get('rally_point', '(732, 767)')}，负责攻城拆迁任务"
    
    items_text = "、".join(backpack_items[:3]) if backpack_items else "无"
    
    return f"""**【作战军令 - {role}】**

{player_name}将军：

根据{event_info.get('event_date', '9月15号')}{event_info.get('event_time', '早上10点')}的{event_info.get('event_type', '攻城战')}安排，你的任务是：{task}。

你的{main_level}级主力部队战力充足，预备兵{reserve_troops}，携带道具：{items_text}。

请按时参战，为国争光！"""

# 旧的硬编码函数已被LLM驱动的_call_llm_for_content_generation替代
# generate_personalized_order_from_commander函数已移除

def send_military_order(
    player_id: str,
    military_order_content: str,
    order_type: str = "personalized_military_order"
) -> str:
    """
    发送个性化军令
    
    Args:
        player_id: 目标玩家ID
        military_order_content: 军令内容
        order_type: 军令类型
    
    Returns:
        发送结果的JSON字符串
    """
    print(f"--- 军令推送执行 ---")
    print(f"  - 目标玩家: {player_id}")
    print(f"  - 军令类型: {order_type}")
    print(f"  - 内容长度: {len(military_order_content)}字符")
    
    # 模拟发送过程
    import random
    success = random.choice([True, True, True, False])  # 75%成功率
    
    if success:
        result = {
            "status": "success",
            "message": f"个性化军令已成功发送给玩家 {player_id}",
            "order_id": f"MO_{player_id}_{int(datetime.now().timestamp())}",
            "sent_at": datetime.now().isoformat()
        }
    else:
        result = {
            "status": "failed",
            "message": f"军令发送失败：玩家 {player_id} 当前不在线",
            "error_code": "PLAYER_OFFLINE"
        }
    
    return json.dumps(result, ensure_ascii=False)