<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>


<h2>${_('Language')} ${ctx.name}</h2>

<ul>
% for identifier in ctx.identifiers:
<li>${identifier.id}</li>
% endfor
</ul>