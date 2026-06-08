# fix_sudoers.py
import asyncio
from Elevenyts import db

async def fix():
    # Deleted account IDs များ
    deleted_ids = [8779269421, 7181902806, 8897382127]
    
    # လက်ရှိ sudoers စာရင်းကိုယူ
    current_sudoers = await db.get_sudoers()
    print(f"လက်ရှိ sudoers: {current_sudoers}")
    
    # တစ်ခုချင်းစီဖျက်မယ်
    for uid in deleted_ids:
        if uid in current_sudoers:
            await db.del_sudo(uid)
            print(f"ဖျက်လိုက်ပြီ: {uid}")
        else:
            print(f"{uid} က sudoers ထဲမှာ မရှိပါ")
    
    # ပြန်စစ်မယ်
    new_sudoers = await db.get_sudoers()
    print(f"\nဖျက်ပြီးနောက် sudoers: {new_sudoers}")

if __name__ == "__main__":
    asyncio.run(fix())
